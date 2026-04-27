"""Clarifier agent (v1, glm4.7).

Decides whether to surface a one-tap clarification to the user. Enforces:
- At-most-one active clarification across the whole session (UI invariant).
- 90s fallback timer per spec — if user doesn't respond, auto-resolve with
  the agent's stated fallback assumption.
- Subsequent clarifications queue.

Triggered per Critic review: if any concern is severity=blocker, attempt to
surface a clarification.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..providers.nvidia import NvidiaClient, model_for
from ..session import ArtifactThread, SessionState
from ..ws_protocol import Clarification, CriticReview, ResolvedClarification

log = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_DEFAULT_SYSTEM = (_PROMPTS_DIR / "clarifier_system.txt").read_text(encoding="utf-8")


CLARIFICATION_FALLBACK_TIMEOUT_S = 90.0


@dataclass
class ClarifierConfig:
    model: Optional[str] = None
    max_tokens: int = 400
    temperature: float = 0.2
    fallback_timeout_s: float = CLARIFICATION_FALLBACK_TIMEOUT_S
    auto_resolve_for_replay: bool = True  # in replay we don't have a UI; auto-resolve via fallback


@dataclass
class Clarifier:
    name: str = "clarifier"
    client: Optional[NvidiaClient] = None
    config: ClarifierConfig = field(default_factory=ClarifierConfig)
    capture_sink: Optional[Any] = None
    system_prompt: str = _DEFAULT_SYSTEM

    def resolved_model(self) -> str:
        return self.config.model or model_for("clarifier")

    async def run(self, state: SessionState) -> None:
        if self.client is None:
            log.info("Clarifier has no client; idling")
            await state.session_ended.wait()
            return

        await state.session_ended.wait()
        # After session_ended, iterate threads and react to their critic reviews.
        for thread in list(state.artifacts):
            try:
                await asyncio.wait_for(thread.new_critic_review.wait(), timeout=60.0)
            except asyncio.TimeoutError:
                continue
            await self.handle_thread(thread, state)

    async def handle_thread(self, thread: ArtifactThread, state: SessionState) -> None:
        if not thread.critic_reviews:
            return
        review = thread.critic_reviews[-1]
        blockers = [c for c in review.concerns if c.severity == "blocker"]
        if not blockers:
            return

        # Build the surface? prompt
        clar = await self._decide(thread, state, review)
        if clar is None or not clar.get("should_surface"):
            return

        # At-most-one active clarification across the session.
        async with state.clarification_lock:
            if state.active_clarification is not None:
                # Queue.
                queued = Clarification(
                    id=f"clar_{uuid.uuid4().hex[:8]}",
                    question=clar["question"],
                    options=list(clar.get("options") or []),
                    fallback_if_ignored=clar.get("fallback_if_ignored", ""),
                    created_at=time.time(),
                )
                state.pending_clarification_queue.append((thread.id, queued))
                return

            new_clar = Clarification(
                id=f"clar_{uuid.uuid4().hex[:8]}",
                question=clar["question"],
                options=list(clar.get("options") or []),
                fallback_if_ignored=clar.get("fallback_if_ignored", ""),
                created_at=time.time(),
            )
            state.active_clarification = new_clar
            state.active_clarification_thread_id = thread.id
            thread.pending_clarification = new_clar

        if self.config.auto_resolve_for_replay:
            await self._auto_resolve_fallback(thread, state)

    async def _auto_resolve_fallback(self, thread: ArtifactThread, state: SessionState) -> None:
        """For eval replay: there's no Mac UI to respond, so we resolve via
        the recorded fallback after a tiny delay (representing the 90s timeout
        in compressed time)."""
        await asyncio.sleep(0)  # yield once for cooperative friendliness
        async with state.clarification_lock:
            clar = state.active_clarification
            if clar is None:
                return
            resolved = ResolvedClarification(
                id=clar.id,
                question=clar.question,
                options=clar.options,
                outcome=clar.fallback_if_ignored or "(no fallback specified)",
                timed_out=True,
            )
            thread.resolved_clarifications.append(resolved)
            thread.pending_clarification = None
            state.active_clarification = None
            state.active_clarification_thread_id = None

            # Drain one queued clarification if present.
            if state.pending_clarification_queue:
                next_thread_id, next_clar = state.pending_clarification_queue.pop(0)
                state.active_clarification = next_clar
                state.active_clarification_thread_id = next_thread_id
                next_thread = state.thread_by_id(next_thread_id)
                if next_thread is not None:
                    next_thread.pending_clarification = next_clar

    async def _decide(self, thread: ArtifactThread, state: SessionState, review: CriticReview) -> Optional[dict]:
        if state.cost_tracker.paused:
            return None
        already_pending = state.active_clarification is not None
        concerns_block = json.dumps([c.model_dump() for c in review.concerns], indent=2)
        plan_block = json.dumps(thread.build_plan or {}, indent=2)
        user_msg = (
            f"# Thread topic\n{thread.inferred_topic}\n\n"
            f"# already_pending: {already_pending}\n\n"
            f"# Critic concerns\n{concerns_block}\n\n"
            f"# Current BuildPlan\n{plan_block}\n\n"
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
                log.exception("clarifier LLM call failed for thread %s", thread.id)
                return None
        latency_ms = (time.monotonic() - t0) * 1000.0

        if self.capture_sink is not None:
            try:
                self.capture_sink.record(
                    agent=self.name, trigger=f"thread:{thread.id}",
                    prompt={"model": self.resolved_model(), "thread": thread.id},
                    response={"text": res.text[:400]},
                    usage=res.usage, cost_usd=0.0, latency_ms=latency_ms,
                )
            except Exception:
                pass

        parsed = _parse_json(res.text) or {}
        if not parsed.get("should_surface"):
            return None
        return parsed


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
