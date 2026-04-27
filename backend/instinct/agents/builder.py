"""Builder agent (v1 push, qwen3-coder-480b).

Per-thread BuildPlan generator. Fires once per thread at session_end (and
optionally on a timer / new decision in production); produces a recipe-typed
BuildPlan via structured output. Revises the prior version when present.

The Builder doesn't pick the archetype — Synthesis does. But for v1 push we
let Builder seed it via heuristic on the first call so the run is self-
contained even when Synthesis hasn't run yet.
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
from ..ws_protocol import SpecDecision, SpecDraft, SpecOpenQuestion, SpecRequirement, Utterance, UtteranceTag

log = logging.getLogger(__name__)


_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_DEFAULT_SYSTEM = (_PROMPTS_DIR / "builder_system.txt").read_text(encoding="utf-8")


# Tagger intent labels that the Builder should consume. Asides/brainstorms
# stay in the transcript but don't shape the BuildPlan.
_BUILDER_INTENTS = {"decision", "proposal", "walked_back", "question"}


@dataclass
class BuilderConfig:
    model: Optional[str] = None
    max_tokens: int = 1500
    temperature: float = 0.3
    fire_at_session_end: bool = True


@dataclass
class Builder:
    """v1 Builder. Produces recipe-typed BuildPlans."""

    name: str = "builder"
    client: Optional[NvidiaClient] = None
    config: BuilderConfig = field(default_factory=BuilderConfig)
    capture_sink: Optional[Any] = None
    system_prompt: str = _DEFAULT_SYSTEM

    def resolved_model(self) -> str:
        return self.config.model or model_for("builder")

    async def run(self, state: SessionState) -> None:
        if self.client is None:
            log.info("Builder has no client; idling")
            await state.session_ended.wait()
            return
        # Fire-on-session-end pattern keeps replay deterministic. Real-time
        # meetings would also schedule periodic builds.
        await state.session_ended.wait()
        if self.config.fire_at_session_end:
            await state.ensure_default_thread()
            for thread in list(state.artifacts):
                if not thread.utterance_ids:
                    continue
                try:
                    await self.build_for_thread(thread, state)
                except Exception:
                    log.exception("builder failed for thread %s", thread.id)

    async def build_for_thread(self, thread: ArtifactThread, state: SessionState) -> None:
        if state.cost_tracker.paused:
            log.warning("cost ceiling — skipping builder for thread %s", thread.id)
            return

        archetype = thread.archetype or self._seed_archetype(thread, state)
        thread.archetype = archetype

        # Local import to avoid recipes ↔ session circular at module load.
        from ..recipes import get as get_recipe
        recipe = get_recipe(archetype)

        prior_plan = thread.build_plan
        plan_dict = await self._call_llm(thread, state, recipe, prior_plan)
        if plan_dict is None:
            return

        # Normalize archetype field on the dict.
        plan_dict["archetype"] = archetype

        # Validate via recipe's BuildPlan class. On failure, keep the raw dict
        # so downstream can still inspect.
        try:
            recipe.parse_build_plan(plan_dict)
            valid = True
        except Exception:
            log.warning("builder output failed schema validation for thread %s", thread.id)
            valid = False

        async with thread.lock:
            thread.build_plan = plan_dict
            # Maintain a SpecDraft "version" alongside for legacy scoring.
            version = SpecDraft(
                version=len(thread.builder_versions) + 1,
                title=str(plan_dict.get("title") or plan_dict.get("name") or thread.inferred_topic),
                summary=str(plan_dict.get("description") or plan_dict.get("summary") or ""),
                requirements=[],
                open_questions=[],
                decisions_made=_decisions_from_plan(plan_dict),
                out_of_scope=list(plan_dict.get("out_of_scope") or []),
                confidence_overall=0.7 if valid else 0.5,
            )
            thread.builder_versions.append(version)
        thread.new_builder_version.set()

    async def _call_llm(
        self,
        thread: ArtifactThread,
        state: SessionState,
        recipe: Any,
        prior_plan: Optional[dict],
    ) -> Optional[dict]:
        # Build the message payload.
        schema_block = json.dumps(
            recipe.build_plan_class.model_json_schema(), indent=2,
        )
        prior_block = (
            f"\n\nPrevious BuildPlan (revise this; don't regenerate):\n"
            f"{json.dumps(prior_plan, indent=2)}"
            if prior_plan else "\n\n(No previous version — produce v1.)"
        )
        recipe_template = recipe.builder_prompt_template()

        utts = _utterances_for_thread(thread, state)
        tagged_block = _format_tagged(utts, state.tags)
        vision_block = _format_vision(state)
        steering_block = _format_steering(thread, state)
        user_ctx = state.user_context or "(none)"

        user_msg = (
            f"# Recipe\n{recipe.archetype}\n\n"
            f"# Recipe BuildPlan JSON schema\n{schema_block}\n\n"
            f"# Recipe-specific guidance\n{recipe_template}\n\n"
            f"# Filtered tagged transcript (intents that shape the build)\n"
            f"{tagged_block}\n\n"
            f"# Vision observations during the meeting\n{vision_block}\n\n"
            f"# User steering notes\n{steering_block}\n\n"
            f"# Team context\n{user_ctx}{prior_block}\n\n"
            f"# Output\nJSON only — one BuildPlan object matching the schema above."
        )
        messages = [
            {"role": "system", "content": self.system_prompt},
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
                log.exception("builder LLM call failed for thread %s", thread.id)
                return None
        latency_ms = (time.monotonic() - t0) * 1000.0

        if self.capture_sink is not None:
            try:
                self.capture_sink.record(
                    agent=self.name,
                    trigger=f"thread:{thread.id}",
                    prompt={"model": self.resolved_model(), "thread": thread.id, "archetype": recipe.archetype},
                    response={"text": res.text[:600]},
                    usage=res.usage,
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                )
            except Exception:
                pass

        parsed = _parse_json(res.text)
        return parsed

    def _seed_archetype(self, thread: ArtifactThread, state: SessionState) -> str:
        """When the thread doesn't yet have a chosen archetype, pick the
        recipe with the highest heuristic match score."""
        from ..recipes import all_recipes

        # Build a thread-scoped subview by filtering tags/transcript by thread membership.
        scored = sorted(
            ((r.archetype, r.heuristic_match_score(_thread_view(thread, state)))
             for r in all_recipes()),
            key=lambda kv: kv[1],
            reverse=True,
        )
        return scored[0][0] if scored and scored[0][1] > 0 else "spec_doc"


# --- helpers ---


class _ThreadView:
    """A SessionState-shaped lightweight view scoped to a single thread.
    Lets recipes' heuristic_match_score work without modification."""

    def __init__(self, thread: ArtifactThread, state: SessionState) -> None:
        self.transcript = [u for u in state.transcript if u.id in set(thread.utterance_ids)]
        self.vision_observations = state.vision_observations
        self.tags = state.tags
        self.user_context = state.user_context


def _thread_view(thread: ArtifactThread, state: SessionState) -> _ThreadView:
    return _ThreadView(thread, state)


def _utterances_for_thread(thread: ArtifactThread, state: SessionState) -> list[Utterance]:
    s = set(thread.utterance_ids)
    return [u for u in state.transcript if u.id in s]


def _format_tagged(utts: list[Utterance], tags: dict[str, UtteranceTag]) -> str:
    if not utts:
        return "(no utterances yet)"
    out = []
    for u in utts:
        tag = tags.get(u.id)
        intent = tag.intent if tag else "context"
        if intent not in _BUILDER_INTENTS:
            continue
        topic = tag.topic if tag else ""
        out.append(f"  [{intent:<11s}] [{u.id}] {u.speaker}: {u.text}  ({topic})")
    if not out:
        # Fallback: include all utterances if no Builder-relevant tags exist.
        for u in utts:
            out.append(f"  [untagged ] [{u.id}] {u.speaker}: {u.text}")
    return "\n".join(out)


def _format_vision(state: SessionState) -> str:
    if not state.vision_observations:
        return "(no vision frames observed)"
    out = []
    for v in state.vision_observations[-10:]:
        if v.summary == "(unchanged)":
            continue
        out.append(f"  [{v.timestamp_seconds:.0f}s] [{v.content_type}] {v.summary}")
    return "\n".join(out) if out else "(no novel vision frames)"


def _format_steering(thread: ArtifactThread, state: SessionState) -> str:
    relevant = [
        n for n in state.steering_notes
        if not n.get("target_thread_id") or n.get("target_thread_id") == thread.id
    ]
    if not relevant:
        return "(no steering notes)"
    return "\n".join(f"  - {n.get('text','')}" for n in relevant)


def _decisions_from_plan(plan: dict) -> list[SpecDecision]:
    """Best-effort extraction of decision-shaped items from a recipe BuildPlan.

    Recipes expose decisions differently — scheduled_python_script's `name`
    is one decision, streamlit's chart specs are several, etc. For scoring
    purposes we want a list of decision-text strings.
    """
    out: list[SpecDecision] = []

    def add(text: str) -> None:
        if not text:
            return
        out.append(SpecDecision(id=f"d{len(out)+1}", text=text, source_utterances=[]))

    # Generic: a top-level "decisions" array
    for d in plan.get("decisions") or []:
        add(d if isinstance(d, str) else str(d))

    # scheduled_python_script
    if plan.get("archetype") == "scheduled_python_script":
        if plan.get("name"):
            add(f"Schedule a {plan['name']} job ({plan.get('schedule_cron','')})")
        for inp in plan.get("inputs") or []:
            add(f"Input source: {inp}")
        for outp in plan.get("outputs") or []:
            add(f"Output: {outp}")

    # streamlit_dashboard
    if plan.get("archetype") == "streamlit_dashboard":
        if plan.get("title"):
            add(f"Dashboard: {plan['title']}")
        for src in plan.get("data_sources") or []:
            name = src.get("name") if isinstance(src, dict) else str(src)
            kind = src.get("kind") if isinstance(src, dict) else ""
            add(f"Data source: {name} ({kind})".strip())
        for ch in plan.get("charts") or []:
            t = ch.get("title") if isinstance(ch, dict) else str(ch)
            ct = ch.get("chart_type") if isinstance(ch, dict) else ""
            add(f"Chart: {t} ({ct})".strip())
        for f in plan.get("filters") or []:
            n = f.get("name") if isinstance(f, dict) else str(f)
            add(f"Filter: {n}")

    # linear_epic — populated when that recipe lands
    if plan.get("archetype") == "linear_epic":
        if plan.get("title"):
            add(f"Epic: {plan['title']}")
        for st in plan.get("sub_tickets") or []:
            ttl = st.get("title") if isinstance(st, dict) else str(st)
            add(f"Sub-ticket: {ttl}")

    return out


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
