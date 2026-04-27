"""Embeddings layer (v1 foundation).

Two embedders:
- TextEmbedder via nvidia/llama-nemotron-embed-1b-v2 (utterances, decisions, etc.)
- CodeEmbedder via nvidia/nv-embedcode-7b-v1 (generated artifact source)

Both wrap the same NvidiaClient. Putting these in foundation (rather than
Phase B) means corpus + sidecar can write embeddings from day one — no
retrofitting later when team memory ships.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .providers.nvidia import NvidiaClient, model_for

log = logging.getLogger(__name__)


@dataclass
class TextEmbedder:
    """Embeds general text. Defaults to nvidia/llama-nemotron-embed-1b-v2."""

    client: NvidiaClient
    model: Optional[str] = None  # resolved lazily from env

    def resolved_model(self) -> str:
        return self.model or model_for("text_embed")

    async def embed(self, texts: list[str], *, input_type: str = "passage") -> list[list[float]]:
        """Returns one vector per input. `input_type` is "passage" for indexed
        corpus content or "query" for retrieval queries."""
        if not texts:
            return []
        result = await self.client.embed(
            model=self.resolved_model(), input=texts, input_type=input_type,
        )
        return result.vectors


@dataclass
class CodeEmbedder:
    """Embeds source code. Defaults to nvidia/nv-embedcode-7b-v1."""

    client: NvidiaClient
    model: Optional[str] = None

    def resolved_model(self) -> str:
        return self.model or model_for("code_embed")

    async def embed(self, sources: list[str]) -> list[list[float]]:
        if not sources:
            return []
        result = await self.client.embed(model=self.resolved_model(), input=sources)
        return result.vectors
