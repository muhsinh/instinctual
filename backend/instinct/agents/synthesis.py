"""Synthesis agent (v1, deepseek-v3.2).

End-of-meeting one-shot per thread. Confirms archetype, polishes the
Builder's latest BuildPlan, emits FinalSpec, hands BuildPlan off to the
Claude Code subprocess driver (when configured).
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
from ..ws_protocol import FinalSpec

log = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_DEFAULT_SYSTEM = (_PROMPTS_DIR / "synthesis_system.txt").read_text(encoding="utf-8")


@dataclass
class SynthesisConfig:
    model: Optional[str] = None
    max_tokens: int = 2500
    temperature: float = 0.2


@dataclass
class Synthesis:
    name: str = "synthesis"
    client: Optional[NvidiaClient] = None
    config: SynthesisConfig = field(default_factory=SynthesisConfig)
    capture_sink: Optional[Any] = None
    system_prompt: str = _DEFAULT_SYSTEM

    # Optional. When set, Synthesis hands each thread's BuildPlan off to the
    # subprocess driver after producing the FinalSpec.
    claude_code_driver: Optional[Any] = None

    def resolved_model(self) -> str:
        return self.config.model or model_for("synthesis")

    async def run_once(self, state: SessionState) -> Optional[FinalSpec]:
        if self.client is None:
            log.info("Synthesis has no client; producing nothing")
            return None

        await state.ensure_default_thread()
        first_spec: Optional[FinalSpec] = None
        for thread in list(state.artifacts):
            if not thread.utterance_ids:
                continue
            spec = await self.synthesize_thread(thread, state)
            if spec and first_spec is None:
                first_spec = spec

            # Hand off to subprocess driver if wired.
            if self.claude_code_driver is not None and spec is not None:
                try:
                    await self.claude_code_driver.run(thread=thread, state=state)
                except Exception:
                    log.exception("claude code driver failed for thread %s", thread.id)
        return first_spec

    async def synthesize_thread(self, thread: ArtifactThread, state: SessionState) -> Optional[FinalSpec]:
        if state.cost_tracker.paused:
            return None

        from ..recipes import all_recipes, get as get_recipe

        archetype_keys = [r.archetype for r in all_recipes()]
        latest_builder = thread.builder_versions[-1] if thread.builder_versions else None
        latest_plan = thread.build_plan or {}

        # Pick a tentative archetype if not set so we can give the model a schema.
        tentative = thread.archetype or (latest_plan.get("archetype")) or "spec_doc"
        recipe = get_recipe(tentative)
        schema_block = json.dumps(recipe.build_plan_class.model_json_schema(), indent=2)
        archetype_descs = json.dumps([
            {"archetype": r.archetype, "description": r.description}
            for r in all_recipes()
        ], indent=2)

        utt_view = "\n".join(
            f"  [{u.id}] {u.speaker}: {u.text}"
            for u in state.transcript if u.id in set(thread.utterance_ids)
        ) or "(no utterances)"
        critics = json.dumps([r.model_dump() for r in thread.critic_reviews[-2:]], indent=2)
        clarifications = json.dumps([
            {"question": rc.question, "outcome": rc.outcome, "timed_out": rc.timed_out}
            for rc in thread.resolved_clarifications
        ], indent=2)

        user_msg = (
            f"# Available archetypes\n{archetype_descs}\n\n"
            f"# Thread topic\n{thread.inferred_topic}\n\n"
            f"# Tentative archetype\n{tentative}\n\n"
            f"# Tentative archetype's BuildPlan schema\n{schema_block}\n\n"
            f"# Latest Builder BuildPlan (revise this)\n{json.dumps(latest_plan, indent=2)}\n\n"
            f"# Recent Critic reviews\n{critics}\n\n"
            f"# Resolved clarifications\n{clarifications}\n\n"
            f"# Thread utterances\n{utt_view}\n\n"
            "Output JSON only — exactly the shape described in the system prompt."
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
                log.exception("synthesis LLM call failed for thread %s", thread.id)
                return None
        latency_ms = (time.monotonic() - t0) * 1000.0

        if self.capture_sink is not None:
            try:
                self.capture_sink.record(
                    agent=self.name, trigger=f"thread:{thread.id}",
                    prompt={"model": self.resolved_model(), "thread": thread.id},
                    response={"text": res.text[:600]},
                    usage=res.usage, cost_usd=0.0, latency_ms=latency_ms,
                )
            except Exception:
                pass

        parsed = _parse_json(res.text) or {}
        archetype = str(parsed.get("archetype") or tentative)
        if archetype not in archetype_keys:
            archetype = tentative

        plan = parsed.get("build_plan") or latest_plan or {}
        if isinstance(plan, dict):
            plan["archetype"] = archetype

        spec = FinalSpec(
            final_spec_markdown=str(parsed.get("final_spec_markdown") or ""),
            executive_summary=str(parsed.get("executive_summary") or ""),
            decisions_made=[str(x) for x in parsed.get("decisions_made") or []],
            open_questions=[str(x) for x in parsed.get("open_questions") or []],
            assumptions_inferred=[str(x) for x in parsed.get("assumptions_inferred") or []],
            suggested_next_steps=[str(x) for x in parsed.get("suggested_next_steps") or []],
            confidence_notes=str(parsed.get("confidence_notes") or ""),
            archetype=archetype,
            archetype_confidence=float(parsed.get("archetype_confidence") or 0.0),
            build_plan=plan if isinstance(plan, dict) else None,
        )
        async with thread.lock:
            thread.archetype = archetype
            thread.archetype_confidence = spec.archetype_confidence
            thread.build_plan = plan if isinstance(plan, dict) else None
            thread.final_spec = spec
        return spec


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
