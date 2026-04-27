"""Critic agent (v1, glm4.7).

Per-thread review of the latest Builder BuildPlan. Internal only — output
flows to the Clarifier which decides whether to surface anything to the user.
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
from ..ws_protocol import CriticConcern, CriticReview, Utterance, UtteranceTag

log = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_DEFAULT_SYSTEM = (_PROMPTS_DIR / "critic_system.txt").read_text(encoding="utf-8")


@dataclass
class CriticConfig:
    model: Optional[str] = None
    max_tokens: int = 800
    temperature: float = 0.2
    wait_for_builder_timeout_s: float = 60.0


@dataclass
class Critic:
    name: str = "critic"
    client: Optional[NvidiaClient] = None
    config: CriticConfig = field(default_factory=CriticConfig)
    capture_sink: Optional[Any] = None
    system_prompt: str = _DEFAULT_SYSTEM

    def resolved_model(self) -> str:
        return self.config.model or model_for("clarifier")  # glm4.7 — same family for both

    async def run(self, state: SessionState) -> None:
        if self.client is None:
            log.info("Critic has no client; idling")
            await state.session_ended.wait()
            return

        await state.session_ended.wait()
        for thread in list(state.artifacts):
            try:
                await asyncio.wait_for(
                    thread.new_builder_version.wait(),
                    timeout=self.config.wait_for_builder_timeout_s,
                )
            except asyncio.TimeoutError:
                log.info("critic: timeout waiting for builder on thread %s", thread.id)
                continue
            await self.review_thread(thread, state)

    async def review_thread(self, thread: ArtifactThread, state: SessionState) -> None:
        if state.cost_tracker.paused:
            return
        if not thread.build_plan:
            return

        utts = [u for u in state.transcript if u.id in set(thread.utterance_ids)]
        tagged_block = _format_tagged(utts, state.tags)
        plan_block = json.dumps(thread.build_plan, indent=2)

        user_msg = (
            f"# Thread topic\n{thread.inferred_topic}\n\n"
            f"# Current BuildPlan\n{plan_block}\n\n"
            f"# Filtered transcript\n{tagged_block}\n\n"
            f"# Vision observations\n{_format_vision(state)}\n\n"
            "Output JSON only."
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
                log.exception("critic LLM call failed for thread %s", thread.id)
                return
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
        concerns_raw = parsed.get("concerns") or []
        concerns: list[CriticConcern] = []
        for c in concerns_raw:
            try:
                concerns.append(CriticConcern(
                    type=c.get("type", "unstated_assumption"),
                    severity=c.get("severity", "warning"),
                    text=str(c.get("text", "")),
                    suggested_clarification=c.get("suggested_clarification"),
                ))
            except Exception:
                continue

        review = CriticReview(
            reviewing_version=len(thread.builder_versions),
            concerns=concerns,
        )
        async with thread.lock:
            thread.critic_reviews.append(review)
        thread.new_critic_review.set()


def _format_tagged(utts: list[Utterance], tags: dict[str, UtteranceTag]) -> str:
    if not utts:
        return "(no utterances)"
    out = []
    for u in utts:
        tag = tags.get(u.id)
        intent = tag.intent if tag else "context"
        if intent in ("aside", "context", "brainstorm"):
            continue
        out.append(f"  [{intent}] [{u.id}] {u.speaker}: {u.text}")
    return "\n".join(out) or "(no decision-shape utterances)"


def _format_vision(state: SessionState) -> str:
    obs = [v for v in state.vision_observations if v.summary != "(unchanged)"]
    if not obs:
        return "(none)"
    return "\n".join(f"  [{v.timestamp_seconds:.0f}s] [{v.content_type}] {v.summary}" for v in obs[-6:])


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
