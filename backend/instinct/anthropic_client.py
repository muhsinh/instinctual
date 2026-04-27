"""Anthropic API wrapper.

Responsibilities:
- Pass through prompts shaped with explicit cache_control breakpoints (per-agent).
- Record token usage (including cache hits/misses) into a CostTracker.
- Exponential-backoff retries on rate-limit / overload errors.
- Three modes: LIVE (call API), RECORD (call API + persist response), PLAYBACK
  (replay persisted response, never call API). PLAYBACK is what the eval harness
  uses for cheap CI runs and reproducible prompt-iteration sessions.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic
from anthropic import APIStatusError, RateLimitError

from .cost_tracker import CostTracker

log = logging.getLogger(__name__)


class AnthropicMode(str, Enum):
    LIVE = "live"
    RECORD = "record"
    PLAYBACK = "playback"


@dataclass
class AnthropicCall:
    """One invocation. `system` and `messages` use Anthropic SDK shape directly.

    Cache_control breakpoints belong on the relevant blocks within `system` or
    `messages`; the caller controls placement so each agent can shape its own
    prompt without wrapper magic.
    """

    model: str
    system: list[dict[str, Any]]
    messages: list[dict[str, Any]]
    max_tokens: int = 1024
    temperature: float = 1.0
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class CallResult:
    text: str
    usage: dict[str, int]
    stop_reason: str | None
    raw: Any | None = None


class AnthropicClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        mode: AnthropicMode = AnthropicMode.LIVE,
        recordings_dir: Path | None = None,
        max_retries: int = 5,
    ) -> None:
        self.mode = mode
        self.recordings_dir = recordings_dir
        self.max_retries = max_retries

        if mode is not AnthropicMode.PLAYBACK:
            key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY missing; set it in env or pass api_key. "
                    "Use AnthropicMode.PLAYBACK to run without an API key."
                )
            self._client: AsyncAnthropic | None = AsyncAnthropic(api_key=key)
        else:
            self._client = None

        if mode in (AnthropicMode.RECORD, AnthropicMode.PLAYBACK):
            if recordings_dir is None:
                raise ValueError(f"{mode.value} mode requires recordings_dir")
            recordings_dir.mkdir(parents=True, exist_ok=True)

    async def call(self, call: AnthropicCall, *, cost_tracker: CostTracker) -> CallResult:
        if cost_tracker.paused:
            raise RuntimeError("cost_tracker is paused (ceiling reached); refusing call")

        cache_key = _hash_call(call)

        if self.mode is AnthropicMode.PLAYBACK:
            result = self._load_recording(cache_key)
            cost_tracker.record(call.model, **result.usage)
            return result

        result = await self._call_with_retry(call)
        cost_tracker.record(call.model, **result.usage)

        if self.mode is AnthropicMode.RECORD:
            self._save_recording(cache_key, call, result)

        return result

    async def _call_with_retry(self, call: AnthropicCall) -> CallResult:
        assert self._client is not None  # LIVE/RECORD path
        attempt = 0
        while True:
            try:
                resp = await self._client.messages.create(
                    model=call.model,
                    system=call.system,
                    messages=call.messages,
                    max_tokens=call.max_tokens,
                    temperature=call.temperature,
                )
                text_parts = []
                for block in resp.content:
                    if getattr(block, "type", None) == "text":
                        text_parts.append(block.text)
                u = resp.usage
                usage = {
                    "input_tokens": getattr(u, "input_tokens", 0) or 0,
                    "output_tokens": getattr(u, "output_tokens", 0) or 0,
                    "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0,
                    "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
                }
                return CallResult(
                    text="".join(text_parts),
                    usage=usage,
                    stop_reason=getattr(resp, "stop_reason", None),
                    raw=resp,
                )
            except (RateLimitError, APIStatusError) as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                if isinstance(e, APIStatusError) and e.status_code not in (429, 529, 500, 502, 503, 504):
                    raise
                delay = min(20.0, (2 ** (attempt - 1))) + random.uniform(0, 0.5)
                log.warning("anthropic retry %d after %s: sleeping %.1fs", attempt, e.__class__.__name__, delay)
                await asyncio.sleep(delay)

    def _recording_path(self, cache_key: str) -> Path:
        assert self.recordings_dir is not None
        return self.recordings_dir / f"{cache_key}.json"

    def _save_recording(self, cache_key: str, call: AnthropicCall, result: CallResult) -> None:
        path = self._recording_path(cache_key)
        path.write_text(
            json.dumps(
                {
                    "saved_at": time.time(),
                    "call": {
                        "model": call.model,
                        "system": call.system,
                        "messages": call.messages,
                        "max_tokens": call.max_tokens,
                        "temperature": call.temperature,
                    },
                    "result": {
                        "text": result.text,
                        "usage": result.usage,
                        "stop_reason": result.stop_reason,
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def _load_recording(self, cache_key: str) -> CallResult:
        path = self._recording_path(cache_key)
        if not path.exists():
            raise RuntimeError(
                f"PLAYBACK mode but no recording for cache_key={cache_key} at {path}"
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        r = data["result"]
        return CallResult(
            text=r["text"],
            usage=r["usage"],
            stop_reason=r.get("stop_reason"),
            raw=None,
        )


def _hash_call(call: AnthropicCall) -> str:
    payload = json.dumps(
        {
            "model": call.model,
            "system": call.system,
            "messages": call.messages,
            "max_tokens": call.max_tokens,
            "temperature": call.temperature,
        },
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def cache_breakpoint() -> dict[str, Any]:
    """Sentinel dict the agent prompt builders attach to the last block they
    want cached. The wrapper passes it through to the SDK as `cache_control`.
    """
    return {"type": "ephemeral"}
