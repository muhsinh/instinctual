"""Endpoint health monitor (v1 foundation).

Runs daily (or on demand) probes against every configured NVIDIA-routed
endpoint. Logs status, optionally POSTs a JSON report to a webhook.

Why this exists in foundation: the NVIDIA free-tier catalog moves fast.
At time of writing, kimi-k2.5 in the catalog is marked "Deprecation in 4d".
Without this monitor, the first sign of trouble is a production session
crashing on a model that silently disappeared.

CLI:
    uv run python -m instinct.health           # one-shot probe, exit 0 iff all green
    uv run python -m instinct.health --json    # machine-readable output
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Optional

import httpx

from .providers.nvidia import NvidiaClient, NvidiaMode, all_routed_models

log = logging.getLogger(__name__)


@dataclass
class ModelHealth:
    agent: str
    model: str
    status: str  # "green" | "red" | "skipped"
    detail: str = ""
    latency_ms: float = 0.0


@dataclass
class HealthReport:
    timestamp: float = field(default_factory=time.time)
    models: list[ModelHealth] = field(default_factory=list)
    total_green: int = 0
    total_red: int = 0
    total_skipped: int = 0

    @property
    def all_green(self) -> bool:
        return self.total_red == 0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "all_green": self.all_green,
            "totals": {"green": self.total_green, "red": self.total_red, "skipped": self.total_skipped},
            "models": [asdict(m) for m in self.models],
        }


# Probe routing per kind. Embedding/chat get cheap one-shot calls; ASR/PII
# get listed-only checks (proper probes need audio / formatted input).
_LISTED_ONLY = {"transcription", "vision_ocr", "vision_layout", "pii"}


async def probe_all(client: NvidiaClient) -> HealthReport:
    routed = all_routed_models()
    catalog = await client.list_model_ids()

    report = HealthReport()
    for agent, model in routed.items():
        h = await _probe_one(client, agent, model, catalog)
        report.models.append(h)
        if h.status == "green":
            report.total_green += 1
        elif h.status == "red":
            report.total_red += 1
        else:
            report.total_skipped += 1
    return report


async def _probe_one(client: NvidiaClient, agent: str, model: str, catalog: set[str]) -> ModelHealth:
    # Fast path: catalog membership. If the model isn't listed, it's red.
    listed = model in catalog if catalog else None
    if catalog and not listed:
        return ModelHealth(agent=agent, model=model, status="red",
                           detail="not in /v1/models catalog (deprecated or renamed?)")

    if agent in _LISTED_ONLY:
        # No active probe yet; trust catalog.
        return ModelHealth(agent=agent, model=model, status="green" if listed else "skipped",
                           detail="catalog-only (active probe not implemented)")

    if agent in ("text_embed", "code_embed"):
        return await _probe_embed(client, agent, model)

    return await _probe_chat(client, agent, model)


async def _probe_chat(client: NvidiaClient, agent: str, model: str) -> ModelHealth:
    t0 = time.monotonic()
    try:
        await client.chat(
            model=model,
            messages=[{"role": "user", "content": "ok"}],
            max_tokens=1,
            temperature=0.0,
        )
        return ModelHealth(agent=agent, model=model, status="green",
                           latency_ms=(time.monotonic() - t0) * 1000.0)
    except Exception as e:
        return ModelHealth(agent=agent, model=model, status="red",
                           detail=f"{e.__class__.__name__}: {str(e)[:200]}",
                           latency_ms=(time.monotonic() - t0) * 1000.0)


async def _probe_embed(client: NvidiaClient, agent: str, model: str) -> ModelHealth:
    t0 = time.monotonic()
    try:
        await client.embed(model=model, input=["ok"], input_type="query")
        return ModelHealth(agent=agent, model=model, status="green",
                           latency_ms=(time.monotonic() - t0) * 1000.0)
    except Exception as e:
        return ModelHealth(agent=agent, model=model, status="red",
                           detail=f"{e.__class__.__name__}: {str(e)[:200]}",
                           latency_ms=(time.monotonic() - t0) * 1000.0)


async def maybe_post_webhook(report: HealthReport) -> None:
    url = os.environ.get("INSTINCT_HEALTH_WEBHOOK_URL")
    if not url or report.all_green:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as h:
            await h.post(url, json=report.to_dict())
    except Exception:
        log.exception("health webhook POST failed")


def render(report: HealthReport) -> str:
    lines = [f"# endpoint health  ({'GREEN' if report.all_green else 'RED'})"]
    lines.append(f"green={report.total_green} red={report.total_red} skipped={report.total_skipped}")
    lines.append("")
    lines.append(f"{'agent':<14}  {'status':<8} {'lat(ms)':<10}  model")
    for m in report.models:
        lines.append(f"{m.agent:<14}  {m.status:<8} {m.latency_ms:>9.0f}  {m.model}")
        if m.detail:
            lines.append(f"  └─ {m.detail}")
    return "\n".join(lines)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="instinct.health")
    p.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    p.add_argument("--webhook", action="store_true", help="POST to INSTINCT_HEALTH_WEBHOOK_URL on red")
    return p.parse_args(argv)


async def _run(args) -> int:
    # Load .env if present.
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception:
        pass

    if not os.environ.get("NVIDIA_API_KEY"):
        msg = "NVIDIA_API_KEY missing — cannot probe endpoints."
        if args.json:
            print(json.dumps({"error": msg}))
        else:
            print(msg, file=sys.stderr)
        return 2

    client = NvidiaClient(mode=NvidiaMode.LIVE)
    report = await probe_all(client)
    if args.webhook:
        await maybe_post_webhook(report)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(render(report))
    return 0 if report.all_green else 1


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
