"""Top-level session orchestration.

Five concurrent agents share one SessionState. The orchestrator wires them
under asyncio.TaskGroup but isolates failures: per the spec's robustness
guidance, a single failed agent must not crash the session — it just means
that one loop is dead and the others continue.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Optional, Protocol

from .agents.topic_tracker import StubTopicTracker
from .agents.vision import StubVision
from .session import SessionState
from .transcription import TranscriptionStream
from .ws_protocol import FinalSpec

log = logging.getLogger(__name__)


class Agent(Protocol):
    name: str

    async def run(self, state: SessionState) -> None:
        """Long-running loop. Must observe state.session_ended and exit cleanly."""


class SynthesisAgent(Protocol):
    name: str

    async def run_once(self, state: SessionState) -> Optional[FinalSpec]:
        """One-shot at session end. May return None if synthesis fails (logged)."""


@dataclass
class AgentSet:
    tagger: Agent
    builder: Agent
    critic: Agent
    clarifier: Agent
    synthesis: SynthesisAgent
    vision: Optional[Agent] = None         # v1 — peer to transcript stream
    topic_tracker: Optional[Agent] = None  # v1 push — assigns utterances to threads


async def _safe(name: str, coro: Awaitable[None]) -> None:
    """Run a coroutine; log any exception other than CancelledError."""
    try:
        await coro
    except asyncio.CancelledError:
        raise
    except Exception:
        log.exception("%s loop crashed; remaining agents continue", name)


async def transcript_consumer(state: SessionState, transcription: TranscriptionStream) -> None:
    """Pull utterances off the transcription stream, append to state, signal.

    Producer sets `new_utterance` and never clears it. The Tagger clears the
    event after it has snapshotted the transcript so it can re-check whether
    more utterances arrived during processing.
    """
    try:
        async for utt in transcription.utterances():
            async with state.transcript_lock:
                state.transcript.append(utt)
            state.new_utterance.set()
    finally:
        # Stream ended (mocked transcription drained, or real stream closed):
        # signal session end so per-agent loops exit.
        state.session_ended.set()


async def session_loop(
    state: SessionState,
    transcription: TranscriptionStream,
    agents: AgentSet,
) -> Optional[FinalSpec]:
    """Drive a meeting end-to-end.

    Returns the FinalSpec produced by Synthesis, or None on synthesis failure.
    """
    async with asyncio.TaskGroup() as tg:
        tg.create_task(_safe("transcript", transcript_consumer(state, transcription)))
        tg.create_task(_safe(agents.tagger.name, agents.tagger.run(state)))
        tg.create_task(_safe(agents.builder.name, agents.builder.run(state)))
        tg.create_task(_safe(agents.critic.name, agents.critic.run(state)))
        tg.create_task(_safe(agents.clarifier.name, agents.clarifier.run(state)))
        if agents.vision is not None:
            tg.create_task(_safe(agents.vision.name, agents.vision.run(state)))
        if agents.topic_tracker is not None:
            tg.create_task(_safe(agents.topic_tracker.name, agents.topic_tracker.run(state)))

    # All loops exited (session_ended fired and each agent yielded). Run synthesis.
    # Synthesis populates the per-thread final_spec internally; the legacy
    # `state.final_synthesis` property reads it back from the first thread.
    try:
        final = await agents.synthesis.run_once(state)
    except Exception:
        log.exception("synthesis failed")
        final = None

    return final


# --- Stub agents used for the wire-check (plan step 16). ----------------
# These let the harness exercise the orchestrator + capture pipeline before
# real agents exist. Each writes a small amount of structured state so scoring
# produces a sane near-0% report rather than crashing on missing fields.


@dataclass
class StubTagger:
    name: str = "tagger"

    async def run(self, state: SessionState) -> None:
        while not state.session_ended.is_set():
            ended = asyncio.create_task(state.session_ended.wait())
            new_utt = asyncio.create_task(state.new_utterance.wait())
            done, pending = await asyncio.wait(
                {ended, new_utt}, return_when=asyncio.FIRST_COMPLETED
            )
            for t in pending:
                t.cancel()
            if state.session_ended.is_set():
                return
            # Stub: don't actually tag. Real Tagger lands in plan step 17.


@dataclass
class StubBuilder:
    name: str = "builder"

    async def run(self, state: SessionState) -> None:
        while not state.session_ended.is_set():
            try:
                await asyncio.wait_for(state.session_ended.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass


@dataclass
class StubCritic:
    name: str = "critic"

    async def run(self, state: SessionState) -> None:
        await state.session_ended.wait()


@dataclass
class StubClarifier:
    name: str = "clarifier"

    async def run(self, state: SessionState) -> None:
        await state.session_ended.wait()


@dataclass
class StubSynthesis:
    """Wire-check synthesis: classifies via heuristic + emits a recipe build_plan
    using the recipe's stub `build_plan_from_state`, then populates a default
    ArtifactThread so v1 single-thread fixtures behave like the legacy single
    track. Real Synthesis (LLM-driven) replaces both steps."""

    name: str = "synthesis"

    async def run_once(self, state: SessionState) -> Optional[FinalSpec]:
        # Local import to avoid circular.
        from .recipes import classify_heuristic, get as get_recipe

        thread = await state.ensure_default_thread()
        clf = classify_heuristic(state)
        recipe = get_recipe(clf.archetype)
        plan = recipe.build_plan_from_state(state)

        spec = FinalSpec(
            final_spec_markdown="(stub synthesis output)",
            executive_summary="(stub)",
            decisions_made=[],
            open_questions=[],
            assumptions_inferred=[],
            suggested_next_steps=[],
            confidence_notes="stub agents — wire-check only",
            archetype=clf.archetype,
            archetype_confidence=clf.confidence,
            build_plan=plan.model_dump(mode="json"),
        )
        async with thread.lock:
            thread.archetype = clf.archetype
            thread.archetype_confidence = clf.confidence
            thread.build_plan = spec.build_plan
            thread.final_spec = spec
        return spec


def stub_agent_set() -> AgentSet:
    return AgentSet(
        tagger=StubTagger(),
        builder=StubBuilder(),
        critic=StubCritic(),
        clarifier=StubClarifier(),
        synthesis=StubSynthesis(),
        vision=StubVision(),
        topic_tracker=StubTopicTracker(),
    )
