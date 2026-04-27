"""Tagger agent (v1, NVIDIA-routed).

Classifies each new utterance against a rolling 60-second context window via
google/gemma-3n-e2b-it on NVIDIA NIM. Output is a typed UtteranceTag written
into shared SessionState.tags so the Builder can later filter Builder-input
to only decision/proposal/walked_back/question utterances.

Optional integrations:
- PII redactor: every utterance routed through redaction before being written
  to the sidecar. Original text stays in SessionState; only redacted goes
  durable.
- TextEmbedder: utterance embeddings written to the sidecar. Phase B / corpus
  consumes them.
- Sidecar: persistent SQLite, one DB per session run.
- CaptureSink (eval harness): every model call recorded as a JSONL line.

The agent is failure-tolerant. Any exception during a single utterance
processing is logged and the loop moves on — per the spec, robustness >
correctness; one bad call doesn't crash the meeting.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..pii import PIIRedactor
from ..providers.nvidia import NvidiaClient, model_for
from ..session import SessionState
from ..ws_protocol import Utterance, UtteranceTag

log = logging.getLogger(__name__)


_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
_DEFAULT_SYSTEM = (_PROMPTS_DIR / "tagger_system.txt").read_text(encoding="utf-8")


# Rolling context window length in seconds.
DEFAULT_CONTEXT_WINDOW_S = 60.0
# Max utterances to include in rolling context (cap on prompt size).
DEFAULT_CONTEXT_MAX_UTTS = 24


@dataclass
class TaggerConfig:
    model: Optional[str] = None
    context_window_s: float = DEFAULT_CONTEXT_WINDOW_S
    context_max_utts: int = DEFAULT_CONTEXT_MAX_UTTS
    max_tokens: int = 200
    temperature: float = 0.2
    debounce_s: float = 0.0  # 0 = no debounce; spec mentions ~2s for prod


@dataclass
class Tagger:
    """v1 Tagger. Drop-in for orchestrator.AgentSet.tagger."""

    name: str = "tagger"
    client: Optional[NvidiaClient] = None
    config: TaggerConfig = field(default_factory=TaggerConfig)
    redactor: Optional[PIIRedactor] = None
    text_embedder: Optional[Any] = None  # avoid circular import; duck-typed
    sidecar: Optional[Any] = None        # ditto
    capture_sink: Optional[Any] = None   # eval.capture.CaptureSink
    system_prompt: str = _DEFAULT_SYSTEM

    def resolved_model(self) -> str:
        return self.config.model or model_for("tagger")

    async def run(self, state: SessionState) -> None:
        """Drain-first / wait-second loop.

        At max replay speed the transcript_consumer can finish before the
        Tagger task gets its first scheduler slice — so the loop must always
        snapshot+process whatever's pending BEFORE checking session_ended.
        """
        if self.client is None:
            log.info("Tagger has no NvidiaClient; idling until session_ended")
            await state.session_ended.wait()
            return

        last_seen = 0
        while True:
            async with state.transcript_lock:
                new = state.transcript[last_seen:]
                last_seen = len(state.transcript)
            state.new_utterance.clear()

            for u in new:
                if self.config.debounce_s > 0:
                    await asyncio.sleep(self.config.debounce_s)
                await self._handle_utterance(u, state)

            if state.session_ended.is_set():
                return

            ended = asyncio.create_task(state.session_ended.wait())
            new_utt = asyncio.create_task(state.new_utterance.wait())
            await asyncio.wait({ended, new_utt}, return_when=asyncio.FIRST_COMPLETED)
            ended.cancel()
            new_utt.cancel()

    async def _handle_utterance(self, utt: Utterance, state: SessionState) -> None:
        if state.cost_tracker.paused:
            log.warning("cost ceiling reached; tagger skipping %s", utt.id)
            return

        # 1. PII redaction (best-effort) before durable writes.
        redacted_text = utt.text
        entities = []
        if self.redactor is not None:
            try:
                r = await self.redactor.redact(utt.text)
                redacted_text = r.redacted
                entities = r.entities
            except Exception:
                log.exception("pii redaction failed for %s; using raw text", utt.id)

        # 2. Text embedding (best-effort).
        embedding = None
        embedding_model = None
        if self.text_embedder is not None:
            try:
                vecs = await self.text_embedder.embed([redacted_text or utt.text])
                if vecs:
                    embedding = list(vecs[0])
                    embedding_model = self.text_embedder.resolved_model()
            except Exception:
                log.exception("text embedding failed for %s", utt.id)

        # 3. Tagger LLM call.
        rolling = self._rolling_context(state, utt)
        tag, raw_response = await self._classify(utt, rolling, state)

        if tag is not None:
            async with state.tags_lock:
                state.tags[utt.id] = tag

        # 4. Sidecar writes (best-effort).
        if self.sidecar is not None:
            try:
                await self.sidecar.write_utterance(
                    session_id=state.session_id,
                    utterance_id=utt.id,
                    speaker=utt.speaker,
                    timestamp_seconds=utt.timestamp_seconds,
                    raw_text=utt.text,
                    redacted_text=redacted_text,
                    entities=entities,
                    embedding=embedding,
                    embedding_model=embedding_model,
                )
                if tag is not None:
                    await self.sidecar.write_tag(
                        session_id=state.session_id,
                        tag=tag,
                        raw_response=raw_response,
                        model=self.resolved_model(),
                    )
            except Exception:
                log.exception("sidecar write failed for %s", utt.id)

    def _rolling_context(self, state: SessionState, current: Utterance) -> list[Utterance]:
        cutoff = current.timestamp_seconds - self.config.context_window_s
        ctx = [u for u in state.transcript if u.timestamp_seconds >= cutoff and u.id != current.id]
        if len(ctx) > self.config.context_max_utts:
            ctx = ctx[-self.config.context_max_utts:]
        return ctx

    async def _classify(
        self,
        utt: Utterance,
        rolling: list[Utterance],
        state: SessionState,
    ) -> tuple[Optional[UtteranceTag], Optional[str]]:
        rolling_block = self._format_rolling(rolling)
        user_msg = (
            f"Rolling context:\n{rolling_block}\n"
            f"New utterance:\n[{utt.id}] {utt.speaker}: {utt.text}\n"
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
        except Exception as e:
            # Some models don't accept response_format; retry without.
            log.debug("tagger retry without response_format: %s", e)
            try:
                res = await self.client.chat(
                    model=self.resolved_model(),
                    messages=messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
            except Exception:
                log.exception("tagger LLM call failed for %s", utt.id)
                return None, None
        latency_ms = (time.monotonic() - t0) * 1000.0

        if self.capture_sink is not None:
            try:
                self.capture_sink.record(
                    agent=self.name,
                    trigger=f"utterance:{utt.id}",
                    prompt={"model": self.resolved_model(), "rolling_len": len(rolling)},
                    response={"text": res.text[:500]},
                    usage=res.usage,
                    cost_usd=0.0,
                    latency_ms=latency_ms,
                )
            except Exception:
                log.exception("tagger capture sink record failed")

        parsed = _parse_tagger_json(res.text)
        if parsed is None:
            return None, res.text
        try:
            tag = UtteranceTag(
                utterance_id=utt.id,
                speaker=utt.speaker,
                intent=parsed.get("intent", "context"),
                confidence=float(parsed.get("confidence") or 0.0),
                topic=str(parsed.get("topic") or "")[:80],
                references_prior=parsed.get("references_prior") or None,
            )
        except Exception:
            log.warning("tagger output failed validation for %s: %r", utt.id, parsed)
            return None, res.text
        return tag, res.text

    @staticmethod
    def _format_rolling(rolling: list[Utterance]) -> str:
        if not rolling:
            return "(no prior utterances in window)"
        return "\n".join(
            f"[{u.id}] {u.speaker}: {u.text}" for u in rolling
        )

    @staticmethod
    def _user_context_block(state: SessionState) -> str:
        if not state.user_context:
            return ""
        return f"\n\nTeam context (read-only, from ~/.instinct/context.md):\n{state.user_context}\n"


def _parse_tagger_json(text: str) -> Optional[dict[str, Any]]:
    if not text:
        return None
    raw = text.strip()
    # strip fences if present
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # last-ditch: extract first {...} block
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                return None
        return None
