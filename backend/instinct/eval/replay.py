"""Replay CLI (Amendment 5).

Drives a fixture through the orchestrator, captures per-agent JSONL, and
scores against the fixture's bar. Exits non-zero if the bar isn't met.

    uv run python -m instinct.eval.replay <fixture_path> --speed {1x,10x,max}
                                           [--output backend/eval/runs]
                                           [--agents stub|real]

`--agents stub` is the Phase-1 wire-check. `--agents real` will be the
default once Tagger/Builder/Critic/Clarifier/Synthesis exist.

`--audio-input <wav>` (Amendment 5b setup) replaces fixture utterances with
a Deepgram-transcribed audio stream. Phase 1 just verifies the code path; the
flag is wired but Phase-1 fixtures don't ship audio.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

from ..orchestrator import AgentSet, session_loop, stub_agent_set
from ..session import SessionState
from ..transcription import MockedTranscription
from ..user_context import load_user_context
from .capture import RunCapture, run_dir_for
from .fixture import Fixture, load_fixture
from .scorer_metrics import score_run

log = logging.getLogger(__name__)


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="instinct.eval.replay")
    p.add_argument("fixture", help="Fixture directory or fixture.json path")
    p.add_argument("--speed", default="10x", help="1x | 10x | max | <n>x (default 10x)")
    p.add_argument(
        "--output",
        default="eval/runs",
        help="Run output root directory (relative to backend/ dir; default eval/runs)",
    )
    p.add_argument(
        "--agents",
        choices=["stub", "real"],
        default="stub",
        help="Phase-1 wire-check uses stubs; real lands once agents exist",
    )
    p.add_argument(
        "--audio-input",
        default=None,
        help="Phase 2 path: route audio file through Deepgram instead of fixture utterances",
    )
    p.add_argument("--quiet", action="store_true", help="Suppress markdown summary on stdout")
    return p.parse_args(argv)


def _build_agents(kind: str) -> AgentSet:
    if kind == "stub":
        return stub_agent_set()
    raise NotImplementedError(
        "real agents not yet implemented; rerun with --agents stub for the wire-check"
    )


async def _run(state: SessionState, fixture: Fixture, *, speed: str, agents: AgentSet) -> None:
    transcription = MockedTranscription(source=list(fixture.utterances), speed=speed)
    # v1: pre-seed any fixture frames into the session. The Vision agent (when
    # configured) will consume them. Frames are loaded sync up-front for
    # determinism in eval; live capture flows through the WebSocket path.
    if fixture.frames:
        state.screen_frames.extend(fixture.frames)
        state.new_screen_frame.set()
    await session_loop(state, transcription, agents)


def _markdown_summary(report_dict: dict, fixture: Fixture, run_dir: Path, duration_s: float) -> str:
    lines = []
    lines.append(f"# replay {fixture.name}")
    lines.append("")
    lines.append(f"- run dir: `{run_dir}`")
    lines.append(f"- duration: {duration_s:.2f}s")
    verdict = "PASS" if report_dict["passed"] else "FAIL"
    lines.append(f"- verdict: **{verdict}**")
    lines.append(f"- cost: ${report_dict['total_cost_usd']:.4f} (bar ${report_dict['max_cost_usd']:.2f})")
    lines.append("")
    lines.append("| metric | value | threshold | passed |")
    lines.append("|---|---|---|---|")
    for m in report_dict["metrics"]:
        thr = "" if m["threshold"] is None else f"{m['threshold']}"
        passed = "" if m["passed"] is None else ("✓" if m["passed"] else "✗")
        lines.append(f"| {m['name']} | {m['value']} | {thr} | {passed} |")
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = parse_args(argv)

    if args.audio_input is not None:
        # Smoke-test code path only in Phase 1.
        log.warning("--audio-input is wired but Phase 1 has no audio fixtures; skipping for now")

    fixture = load_fixture(args.fixture)
    agents = _build_agents(args.agents)

    output_root = Path(args.output)
    run_dir = run_dir_for(output_root)
    capture = RunCapture(run_dir=run_dir, fixture_name=fixture.name)

    # Snapshot user context (Amendment 4); failure is non-fatal but logged.
    try:
        ctx = load_user_context()
    except Exception as e:
        log.warning("user context unavailable: %s", e)
        ctx = ""

    state = SessionState(session_id=f"replay-{fixture.name}", user_context=ctx)

    t0 = time.monotonic()
    try:
        asyncio.run(_run(state, fixture, speed=args.speed, agents=agents))
    except Exception:
        log.exception("session_loop crashed")
        # Continue to scoring so the run dir is still useful for debugging.
    duration_s = time.monotonic() - t0

    report = score_run(state, fixture)
    report_dict = report.to_dict()

    # Aggregate summary written to summary.json in the fixture run dir.
    summary = {
        "fixture": fixture.name,
        "fixture_path": str(Path(args.fixture).resolve()),
        "run_dir": str(capture.fixture_dir.resolve()),
        "speed": args.speed,
        "agents": args.agents,
        "duration_seconds": round(duration_s, 4),
        "passed": report.passed,
        "score": report_dict,
        "cost": state.cost_tracker.snapshot(),
        "transcript_len": len(state.transcript),
        "tags_count": len(state.tags),
        "builder_versions": len(state.builder_versions),
        "critic_reviews": len(state.critic_reviews),
        "clarifications_resolved": len(state.resolved_clarifications),
        "final_synthesis_present": state.final_synthesis is not None,
    }
    capture.write_summary(summary)

    if not args.quiet:
        print(_markdown_summary(report_dict, fixture, capture.fixture_dir, duration_s))
        print()
        print(json.dumps({"passed": summary["passed"], "cost_usd": summary["cost"]["estimated_cost_usd"]}, indent=2))

    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
