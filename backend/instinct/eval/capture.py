"""Per-agent JSONL capture (Amendment 5).

Layout produced by a single replay run:

    backend/eval/runs/<timestamp>/<fixture_name>/
        tagger.jsonl
        builder.jsonl
        critic.jsonl
        clarifier.jsonl
        synthesis.jsonl
        summary.json

Each *.jsonl line records one agent invocation with prompt, response, token
usage, latency, and cost. summary.json holds aggregate scores + cost + bar
verdict.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# Agent names matching stub_agent_set() / real agents. v1 adds vision.
AGENT_NAMES = ("tagger", "builder", "critic", "clarifier", "synthesis", "vision")


@dataclass
class CallRecord:
    """One agent invocation's worth of data."""

    agent: str
    trigger: str
    prompt: dict[str, Any]
    response: dict[str, Any]
    usage: dict[str, int]
    cost_usd: float
    latency_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class RunCapture:
    """Manages a single run's output directory + per-agent writers."""

    run_dir: Path
    fixture_name: str

    def __post_init__(self) -> None:
        self.fixture_dir.mkdir(parents=True, exist_ok=True)
        # Touch each agent's jsonl so the layout is consistent even when an
        # agent never runs (e.g. wire-check with stubs).
        for name in AGENT_NAMES:
            (self.fixture_dir / f"{name}.jsonl").touch()

    @property
    def fixture_dir(self) -> Path:
        return self.run_dir / self.fixture_name

    def jsonl_path(self, agent: str) -> Path:
        return self.fixture_dir / f"{agent}.jsonl"

    def record(self, rec: CallRecord) -> None:
        path = self.jsonl_path(rec.agent)
        line = json.dumps(
            {
                "agent": rec.agent,
                "trigger": rec.trigger,
                "prompt": rec.prompt,
                "response": rec.response,
                "usage": rec.usage,
                "cost_usd": rec.cost_usd,
                "latency_ms": rec.latency_ms,
                "timestamp": rec.timestamp,
            }
        )
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    def write_summary(self, summary: dict[str, Any]) -> Path:
        path = self.fixture_dir / "summary.json"
        path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return path


def run_dir_for(output_root: Path, *, timestamp: Optional[float] = None) -> Path:
    """Build a `<output_root>/<YYYYmmdd-HHMMSS>` path. Doesn't create it."""
    ts = timestamp if timestamp is not None else time.time()
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(ts))
    return output_root / stamp


@dataclass
class CaptureSink:
    """Optional capture target passed into AnthropicClient calls.

    Agents pass `agent` and `trigger` per call; the sink builds CallRecords
    and forwards to RunCapture. Keeping this thin lets production code run
    without capture by passing sink=None.
    """

    run: RunCapture

    def record(
        self,
        *,
        agent: str,
        trigger: str,
        prompt: dict[str, Any],
        response: dict[str, Any],
        usage: dict[str, int],
        cost_usd: float,
        latency_ms: float,
    ) -> None:
        self.run.record(
            CallRecord(
                agent=agent,
                trigger=trigger,
                prompt=prompt,
                response=response,
                usage=usage,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
            )
        )
