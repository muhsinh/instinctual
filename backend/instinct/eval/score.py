"""Score CLI (Amendment 5).

Reads a previously captured run dir's summary.json and pretty-prints a
markdown report to stdout. Use after `replay` to inspect a run, or to format
older captured runs.

    uv run python -m instinct.eval.score <run_dir>

`<run_dir>` should point at the directory written by replay — i.e. the
`<fixture_name>` directory under `backend/eval/runs/<timestamp>/`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="instinct.eval.score")
    p.add_argument("run_dir", help="Path to a run directory (containing summary.json)")
    return p.parse_args(argv)


def load_summary(run_dir: Path) -> dict:
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"no summary.json in {run_dir}")
    return json.loads(summary_path.read_text(encoding="utf-8"))


def render_markdown(summary: dict) -> str:
    score = summary["score"]
    lines = []
    lines.append(f"# score: {summary['fixture']}")
    lines.append("")
    verdict = "PASS" if summary["passed"] else "FAIL"
    lines.append(f"- verdict: **{verdict}**")
    lines.append(f"- speed: `{summary.get('speed','?')}`  agents: `{summary.get('agents','?')}`")
    lines.append(f"- duration: {summary.get('duration_seconds',0):.2f}s")
    lines.append(f"- cost: ${score['total_cost_usd']:.4f} (bar ${score['max_cost_usd']:.2f})")
    lines.append("")
    lines.append("| metric | value | threshold | passed |")
    lines.append("|---|---|---|---|")
    for m in score["metrics"]:
        thr = "" if m["threshold"] is None else f"{m['threshold']}"
        passed = "" if m["passed"] is None else ("✓" if m["passed"] else "✗")
        lines.append(f"| {m['name']} | {m['value']} | {thr} | {passed} |")
    lines.append("")
    lines.append("## state")
    lines.append(f"- transcript utterances: {summary.get('transcript_len',0)}")
    lines.append(f"- tags: {summary.get('tags_count',0)}")
    lines.append(f"- builder versions: {summary.get('builder_versions',0)}")
    lines.append(f"- critic reviews: {summary.get('critic_reviews',0)}")
    lines.append(f"- clarifications resolved: {summary.get('clarifications_resolved',0)}")
    lines.append(f"- final synthesis present: {summary.get('final_synthesis_present', False)}")
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    run_dir = Path(args.run_dir)
    summary = load_summary(run_dir)
    print(render_markdown(summary))

    # Also write score.json next to the run for machine consumers.
    (run_dir / "score.json").write_text(json.dumps(summary["score"], indent=2), encoding="utf-8")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
