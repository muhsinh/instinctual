"""Per-session cost tracking with prompt-cache awareness.

Pricing constants are USD per million tokens. Sourced from Anthropic public
pricing as of 2025-Q4; update when pricing or models change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ModelKey = Literal["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-7"]


# {model_id: {input, input_cached_write (+25%), input_cached_read (10%), output}}
PRICING_USD_PER_MTOK: dict[str, dict[str, float]] = {
    "claude-haiku-4-5": {
        "input": 1.0,
        "input_cached_write": 1.25,
        "input_cached_read": 0.10,
        "output": 5.0,
    },
    "claude-sonnet-4-6": {
        "input": 3.0,
        "input_cached_write": 3.75,
        "input_cached_read": 0.30,
        "output": 15.0,
    },
    "claude-opus-4-7": {
        "input": 15.0,
        "input_cached_write": 18.75,
        "input_cached_read": 1.50,
        "output": 75.0,
    },
}


@dataclass
class TokenUsage:
    input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0


@dataclass
class CostTracker:
    """Records token usage per model and computes USD estimates.

    The tracker pauses agents when cumulative cost reaches `ceiling_usd`
    (default $5 per spec). Agents must consult `paused` before issuing API
    calls and yield gracefully when set.
    """

    ceiling_usd: float = 5.0
    usage: dict[str, TokenUsage] = field(default_factory=dict)
    paused: bool = False

    def record(
        self,
        model: str,
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_creation_input_tokens: int = 0,
        cache_read_input_tokens: int = 0,
    ) -> None:
        u = self.usage.setdefault(model, TokenUsage())
        u.input_tokens += input_tokens
        u.output_tokens += output_tokens
        u.cache_creation_input_tokens += cache_creation_input_tokens
        u.cache_read_input_tokens += cache_read_input_tokens
        u.calls += 1
        if self.estimated_cost_usd() >= self.ceiling_usd:
            self.paused = True

    def estimated_cost_usd(self) -> float:
        total = 0.0
        for model, u in self.usage.items():
            p = PRICING_USD_PER_MTOK.get(model)
            if p is None:
                continue
            total += u.input_tokens * p["input"] / 1_000_000
            total += u.cache_creation_input_tokens * p["input_cached_write"] / 1_000_000
            total += u.cache_read_input_tokens * p["input_cached_read"] / 1_000_000
            total += u.output_tokens * p["output"] / 1_000_000
        return total

    def snapshot(self) -> dict:
        return {
            "estimated_cost_usd": round(self.estimated_cost_usd(), 6),
            "ceiling_usd": self.ceiling_usd,
            "paused": self.paused,
            "by_model": {
                model: {
                    "input_tokens": u.input_tokens,
                    "cache_creation_input_tokens": u.cache_creation_input_tokens,
                    "cache_read_input_tokens": u.cache_read_input_tokens,
                    "output_tokens": u.output_tokens,
                    "calls": u.calls,
                }
                for model, u in self.usage.items()
            },
        }
