"""Topic Tracker agent (v1 push spec).

Runs alongside the Tagger. For each new utterance, classifies it against
existing ArtifactThreads as one of:
- "continues" the most-recent thread,
- "revisits" an older thread,
- "pivots" to a new topic (spawns a new thread).

Always assigns the utterance to exactly one thread (creating a default thread
if none exist yet). Topic Tracker output is the source of truth for
ArtifactThread.utterance_ids — Builder/Critic/Synthesis filter by thread via
that membership list.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..providers.nvidia import NvidiaClient, model_for
from ..session import ArtifactThread, SessionState
from ..ws_protocol import TopicEvent, Utterance

log = logging.getLogger(__name__)


_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_DEFAULT_SYSTEM = (_PROMPTS_DIR / "topic_tracker_system.txt").read_text(encoding="utf-8")


# How many existing threads to advertise to the model (most recent first).
DEFAULT_THREAD_VISIBILITY = 6
# Rolling utterance window length when describing context to the model.
DEFAULT_CONTEXT_MAX_UTTS = 12


@dataclass
class TopicTrackerConfig:
    model: Optional[str] = None      # default = same as tagger (gemma is fast)
    pivot_threshold: float = 0.7
    thread_visibility: int = DEFAULT_THREAD_VISIBILITY
    context_max_utts: int = DEFAULT_CONTEXT_MAX_UTTS
    max_tokens: int = 200
    temperature: float = 0.2


@dataclass
class TopicTracker:
    name: str = "topic_tracker"
    client: Optional[NvidiaClient] = None
    config: TopicTrackerConfig = field(default_factory=TopicTrackerConfig)
    capture_sink: Optional[Any] = None
    system_prompt: str = _DEFAULT_SYSTEM

    def resolved_model(self) -> str:
        return self.config.model or model_for("tagger")  # gemma — fast + cheap

    async def run(self, state: SessionState) -> None:
        if self.client is None:
            log.info("TopicTracker has no client; deferring all utterances to default thread")
            await state.session_ended.wait()
            await state.ensure_default_thread()
            return

        last_seen = 0
        while True:
            async with state.transcript_lock:
                new = state.transcript[last_seen:]
                last_seen = len(state.transcript)
            state.new_utterance.clear()

            for u in new:
                await self._handle(u, state)

            if state.session_ended.is_set():
                return

            ended = asyncio.create_task(state.session_ended.wait())
            new_utt = asyncio.create_task(state.new_utterance.wait())
            await asyncio.wait({ended, new_utt}, return_when=asyncio.FIRST_COMPLETED)
            ended.cancel()
            new_utt.cancel()

    async def _handle(self, utt: Utterance, state: SessionState) -> None:
        if state.cost_tracker.paused:
            log.warning("cost ceiling reached; topic_tracker skipping %s", utt.id)
            return

        # Bootstrap: if no thread exists, create one and bind this utterance.
        if not state.artifacts:
            thread = await state.spawn_thread(
                inferred_topic="(opening topic)",
                started_at_utterance_id=utt.id,
            )
            async with thread.lock:
                thread.utterance_ids.append(utt.id)
            state.topic_events.append(TopicEvent(
                utterance_id=utt.id,
                kind="pivots",
                confidence=1.0,
                target_thread_id=thread.id,
                inferred_topic=thread.inferred_topic,
                timestamp_seconds=utt.timestamp_seconds,
            ))
            state.new_topic_event.set()
            return

        threads_block = self._format_threads(state)
        rolling_block = self._format_rolling(state, utt)
        user_msg = (
            f"Existing threads: {threads_block}\n"
            f"Recent utterances:\n{rolling_block}\n"
            f"New utterance:\n  [{utt.id}] {utt.speaker}: {utt.text}\n"
            "Output:"
        )
        messages = [
            {"role": "system", "content": self.system_prompt + self._user_context_block(state)},
            {"role": "user", "content": user_msg},
        ]

        t0 = time.monotonic()
        try:
            res = await self.client.chat(
                model=self.resolved_model(),
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                response_format={"type": "json_object"},
            )
        except Exception:
            try:
                res = await self.client.chat(
                    model=self.resolved_model(),
                    messages=messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
            except Exception:
                log.exception("topic_tracker LLM call failed for %s", utt.id)
                # safe default: continue most-recent thread
                await self._assign(state, utt, kind="continues", confidence=0.0,
                                   target_thread_id=state.artifacts[-1].id, topic=None)
                return
        latency_ms = (time.monotonic() - t0) * 1000.0

        if self.capture_sink is not None:
            try:
                self.capture_sink.record(
                    agent=self.name,
                    trigger=f"utterance:{utt.id}",
                    prompt={"model": self.resolved_model(), "threads": len(state.artifacts)},
                    response={"text": res.text[:300]},
                    usage=res.usage,
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                )
            except Exception:
                pass

        parsed = _parse_json(res.text)
        if parsed is None:
            await self._assign(state, utt, kind="continues", confidence=0.0,
                               target_thread_id=state.artifacts[-1].id, topic=None)
            return

        kind = parsed.get("kind", "continues")
        conf = float(parsed.get("confidence") or 0.0)
        target = parsed.get("target_thread_id")
        topic = parsed.get("inferred_topic")

        if kind == "pivots" and conf >= self.config.pivot_threshold:
            await self._assign(state, utt, kind="pivots", confidence=conf,
                               target_thread_id=None, topic=topic or "(new thread)")
        elif kind == "revisits" and target and state.thread_by_id(target):
            await self._assign(state, utt, kind="revisits", confidence=conf,
                               target_thread_id=target, topic=None)
        else:
            # default: continues most-recent thread
            target = target if target and state.thread_by_id(target) else state.artifacts[-1].id
            await self._assign(state, utt, kind="continues", confidence=conf,
                               target_thread_id=target, topic=None)

    async def _assign(
        self,
        state: SessionState,
        utt: Utterance,
        *,
        kind: str,
        confidence: float,
        target_thread_id: Optional[str],
        topic: Optional[str],
    ) -> None:
        if kind == "pivots":
            thread = await state.spawn_thread(
                inferred_topic=topic or "(new thread)",
                started_at_utterance_id=utt.id,
            )
            target_thread_id = thread.id
        else:
            assert target_thread_id is not None
            thread = state.thread_by_id(target_thread_id)
            if thread is None:
                # safety: thread vanished somehow
                thread = await state.spawn_thread(
                    inferred_topic="(default)",
                    started_at_utterance_id=utt.id,
                )
                target_thread_id = thread.id

        async with thread.lock:
            thread.utterance_ids.append(utt.id)

        state.topic_events.append(TopicEvent(
            utterance_id=utt.id,
            kind=kind,
            confidence=confidence,
            target_thread_id=target_thread_id,
            inferred_topic=topic,
            timestamp_seconds=utt.timestamp_seconds,
        ))
        state.new_topic_event.set()

    def _format_threads(self, state: SessionState) -> str:
        recent = state.artifacts[-self.config.thread_visibility:]
        return json.dumps([
            {"id": t.id, "topic": t.inferred_topic, "utterance_count": len(t.utterance_ids)}
            for t in recent
        ])

    def _format_rolling(self, state: SessionState, current: Utterance) -> str:
        cutoff = current.timestamp_seconds - 90.0
        recent = [u for u in state.transcript if u.timestamp_seconds >= cutoff and u.id != current.id]
        if len(recent) > self.config.context_max_utts:
            recent = recent[-self.config.context_max_utts:]
        if not recent:
            return "  (no prior utterances in window)"
        return "\n".join(f"  [{u.id}] {u.speaker}: {u.text}" for u in recent)

    @staticmethod
    def _user_context_block(state: SessionState) -> str:
        if not state.user_context:
            return ""
        return f"\n\nTeam context:\n{state.user_context}\n"


def _parse_json(text: str) -> Optional[dict]:
    if not text:
        return None
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e > s:
            try:
                return json.loads(raw[s:e + 1])
            except json.JSONDecodeError:
                return None
        return None


@dataclass
class StubTopicTracker:
    """Wire-check stub: assigns every utterance to a single default thread."""

    name: str = "topic_tracker"

    async def run(self, state: SessionState) -> None:
        last_seen = 0
        while True:
            async with state.transcript_lock:
                new = state.transcript[last_seen:]
                last_seen = len(state.transcript)
            state.new_utterance.clear()
            if new:
                thread = await state.ensure_default_thread()
                async with thread.lock:
                    for u in new:
                        thread.utterance_ids.append(u.id)
                state.new_topic_event.set()
            if state.session_ended.is_set():
                return
            ended = asyncio.create_task(state.session_ended.wait())
            new_utt = asyncio.create_task(state.new_utterance.wait())
            await asyncio.wait({ended, new_utt}, return_when=asyncio.FIRST_COMPLETED)
            ended.cancel()
            new_utt.cancel()
