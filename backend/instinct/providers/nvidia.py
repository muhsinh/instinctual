"""NVIDIA NIM provider client (v1 default).

Thin OpenAI-compatible wrapper around https://integrate.api.nvidia.com/v1.
Single client serves chat, embeddings, and (later) ASR / vision endpoints
via different model names. Per-agent default models live in DEFAULT_MODELS;
each is overridable via environment variables (INSTINCT_<AGENT>_MODEL).

Three modes mirror the Anthropic wrapper: LIVE (call API), RECORD (call API
and persist response), PLAYBACK (replay persisted, no network). PLAYBACK
keeps tests deterministic and CI cost at $0.
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
from typing import Any, Optional

from openai import APIStatusError, AsyncOpenAI, RateLimitError

log = logging.getLogger(__name__)


NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


# Default model routing per the v1 NVIDIA spec. Overridable via env.
DEFAULT_MODELS: dict[str, str] = {
    "tagger": "google/gemma-3n-e2b-it",
    "builder": "qwen/qwen3-coder-480b-a35b-instruct",
    "critic": "moonshotai/kimi-k2-thinking",
    "clarifier": "z-ai/glm4.7",  # spec had "glm-4.7"; NVIDIA catalog ID is "glm4.7" (no hyphen)
    "synthesis": "deepseek-ai/deepseek-v3.2",
    "vision_ocr": "nvidia/nemotron-ocr-v1",
    "vision_layout": "nvidia/nemotron-page-elements-v3",
    "vision_interp": "mistralai/mistral-large-3-675b-instruct-2512",
    "transcription": "nvidia/nemotron-asr-streaming",
    "text_embed": "nvidia/llama-nemotron-embed-1b-v2",
    "code_embed": "nvidia/nv-embedcode-7b-v1",
    "pii": "nvidia/gliner-pii",
}


_ENV_VAR: dict[str, str] = {
    agent: f"INSTINCT_{agent.upper()}_MODEL" for agent in DEFAULT_MODELS
}


def model_for(agent: str) -> str:
    """Resolve the configured model for an agent slot."""
    if agent not in DEFAULT_MODELS:
        raise KeyError(f"unknown agent slot: {agent}")
    return os.environ.get(_ENV_VAR[agent], DEFAULT_MODELS[agent])


def all_routed_models() -> dict[str, str]:
    """Snapshot of agent → resolved model. Useful for health probes."""
    return {agent: model_for(agent) for agent in DEFAULT_MODELS}


class NvidiaMode(str, Enum):
    LIVE = "live"
    RECORD = "record"
    PLAYBACK = "playback"


@dataclass
class ChatResult:
    text: str
    usage: dict[str, int]
    finish_reason: Optional[str] = None
    raw: Any = None


@dataclass
class EmbedResult:
    vectors: list[list[float]]
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class NvidiaClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        mode: NvidiaMode = NvidiaMode.LIVE,
        recordings_dir: Optional[Path] = None,
        max_retries: int = 5,
        request_timeout_s: float = 60.0,
    ) -> None:
        self.mode = mode
        self.recordings_dir = recordings_dir
        self.max_retries = max_retries

        if mode is not NvidiaMode.PLAYBACK:
            key = api_key or os.environ.get("NVIDIA_API_KEY")
            if not key:
                raise RuntimeError(
                    "NVIDIA_API_KEY missing; set it in env or pass api_key, "
                    "or use NvidiaMode.PLAYBACK."
                )
            self._client: Optional[AsyncOpenAI] = AsyncOpenAI(
                base_url=NVIDIA_BASE_URL, api_key=key, timeout=request_timeout_s,
            )
        else:
            self._client = None

        if mode in (NvidiaMode.RECORD, NvidiaMode.PLAYBACK):
            if recordings_dir is None:
                raise ValueError(f"{mode.value} mode requires recordings_dir")
            recordings_dir.mkdir(parents=True, exist_ok=True)

    # --- chat.completions ---

    async def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 400,
        temperature: float = 0.5,
        response_format: Optional[dict[str, Any]] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> ChatResult:
        cache_key = self._chat_hash(
            model=model, messages=messages, max_tokens=max_tokens,
            temperature=temperature, response_format=response_format,
        )
        if self.mode is NvidiaMode.PLAYBACK:
            return self._load_chat_recording(cache_key)

        result = await self._chat_with_retry(
            model=model, messages=messages, max_tokens=max_tokens,
            temperature=temperature, response_format=response_format, extra=extra,
        )
        if self.mode is NvidiaMode.RECORD:
            self._save_chat_recording(cache_key, model, messages, max_tokens, temperature, response_format, result)
        return result

    async def _chat_with_retry(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
        response_format: Optional[dict[str, Any]],
        extra: Optional[dict[str, Any]],
    ) -> ChatResult:
        assert self._client is not None
        attempt = 0
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        if extra:
            kwargs.update(extra)

        while True:
            try:
                resp = await self._client.chat.completions.create(**kwargs)
                choice = resp.choices[0]
                text = choice.message.content or ""
                usage = self._usage_dict(resp)
                return ChatResult(
                    text=text,
                    usage=usage,
                    finish_reason=getattr(choice, "finish_reason", None),
                    raw=resp,
                )
            except (RateLimitError, APIStatusError) as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                if isinstance(e, APIStatusError) and e.status_code not in (
                    408, 425, 429, 500, 502, 503, 504, 529,
                ):
                    raise
                delay = min(20.0, (2 ** (attempt - 1))) + random.uniform(0, 0.5)
                log.warning(
                    "nvidia retry %d after %s on %s: sleeping %.1fs",
                    attempt, e.__class__.__name__, model, delay,
                )
                await asyncio.sleep(delay)

    @staticmethod
    def _usage_dict(resp: Any) -> dict[str, int]:
        u = getattr(resp, "usage", None)
        if u is None:
            return {}
        return {
            "prompt_tokens": getattr(u, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(u, "completion_tokens", 0) or 0,
            "total_tokens": getattr(u, "total_tokens", 0) or 0,
        }

    # --- embeddings ---

    async def embed(
        self,
        *,
        model: str,
        input: list[str],
        input_type: Optional[str] = None,
    ) -> EmbedResult:
        cache_key = self._embed_hash(model=model, input=input, input_type=input_type)
        if self.mode is NvidiaMode.PLAYBACK:
            return self._load_embed_recording(cache_key)

        assert self._client is not None
        kwargs: dict[str, Any] = {"model": model, "input": input}
        if input_type is not None:
            # NVIDIA NIM embedding models take input_type via extra_body.
            kwargs["extra_body"] = {"input_type": input_type}

        attempt = 0
        while True:
            try:
                resp = await self._client.embeddings.create(**kwargs)
                vectors = [d.embedding for d in resp.data]
                usage = self._usage_dict(resp)
                result = EmbedResult(vectors=vectors, usage=usage, raw=resp)
                if self.mode is NvidiaMode.RECORD:
                    self._save_embed_recording(cache_key, model, input, input_type, result)
                return result
            except (RateLimitError, APIStatusError) as e:
                attempt += 1
                if attempt > self.max_retries:
                    raise
                if isinstance(e, APIStatusError) and e.status_code not in (
                    408, 425, 429, 500, 502, 503, 504, 529,
                ):
                    raise
                delay = min(20.0, (2 ** (attempt - 1))) + random.uniform(0, 0.5)
                log.warning("nvidia embed retry %d (%s): sleeping %.1fs", attempt, e.__class__.__name__, delay)
                await asyncio.sleep(delay)

    # --- list models (cheap probe used by health monitor) ---

    async def list_model_ids(self) -> set[str]:
        assert self._client is not None
        try:
            resp = await self._client.models.list()
            return {m.id for m in resp.data}
        except Exception as e:
            log.warning("models.list failed: %s", e)
            return set()

    # --- recording helpers ---

    @staticmethod
    def _chat_hash(*, model, messages, max_tokens, temperature, response_format) -> str:
        payload = json.dumps(
            {"kind": "chat", "model": model, "messages": messages,
             "max_tokens": max_tokens, "temperature": temperature,
             "response_format": response_format},
            sort_keys=True,
        ).encode()
        return hashlib.sha256(payload).hexdigest()[:16]

    @staticmethod
    def _embed_hash(*, model, input, input_type) -> str:
        payload = json.dumps(
            {"kind": "embed", "model": model, "input": input, "input_type": input_type},
            sort_keys=True,
        ).encode()
        return hashlib.sha256(payload).hexdigest()[:16]

    def _recording_path(self, cache_key: str) -> Path:
        assert self.recordings_dir is not None
        return self.recordings_dir / f"{cache_key}.json"

    def _save_chat_recording(self, cache_key, model, messages, max_tokens, temperature, response_format, result: ChatResult) -> None:
        path = self._recording_path(cache_key)
        path.write_text(json.dumps({
            "saved_at": time.time(),
            "kind": "chat",
            "call": {"model": model, "messages": messages,
                     "max_tokens": max_tokens, "temperature": temperature,
                     "response_format": response_format},
            "result": {"text": result.text, "usage": result.usage,
                       "finish_reason": result.finish_reason},
        }, indent=2), encoding="utf-8")

    def _load_chat_recording(self, cache_key: str) -> ChatResult:
        path = self._recording_path(cache_key)
        if not path.exists():
            raise RuntimeError(f"PLAYBACK: no chat recording for {cache_key} at {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        r = data["result"]
        return ChatResult(text=r["text"], usage=r.get("usage", {}),
                          finish_reason=r.get("finish_reason"), raw=None)

    def _save_embed_recording(self, cache_key, model, input, input_type, result: EmbedResult) -> None:
        path = self._recording_path(cache_key)
        path.write_text(json.dumps({
            "saved_at": time.time(),
            "kind": "embed",
            "call": {"model": model, "input": input, "input_type": input_type},
            "result": {"vectors": result.vectors, "usage": result.usage},
        }, indent=2), encoding="utf-8")

    def _load_embed_recording(self, cache_key: str) -> EmbedResult:
        path = self._recording_path(cache_key)
        if not path.exists():
            raise RuntimeError(f"PLAYBACK: no embed recording for {cache_key} at {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        r = data["result"]
        return EmbedResult(vectors=r["vectors"], usage=r.get("usage", {}), raw=None)
