"""Diff CLI (Amendment 5).

Side-by-side diff of two run dirs' summaries. Useful for "did this prompt
change make things better or worse" iteration.

    uv run python -m instinct.eval.diff <run_dir_a> <run_dir_b>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="instinct.eval.diff")
    p.add_argument("a", help="First run directory")
    p.add_argument("b", help="Second run directory")
    return p.parse_args(argv)


def _load(run_dir: Path) -> dict:
    return json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))


def _fmt_metric(m: dict) -> str:
    return f"{m['value']}" + (f" (thr {m['threshold']})" if m["threshold"] is not None else "")


def render_diff(a: dict, b: dict) -> str:
    lines = []
    lines.append(f"# diff: {a['fixture']} vs {b['fixture']}")
    lines.append("")
    lines.append(f"- A: `{a.get('run_dir','?')}` ({a.get('agents','?')}, {a.get('speed','?')})")
    lines.append(f"- B: `{b.get('run_dir','?')}` ({b.get('agents','?')}, {b.get('speed','?')})")
    lines.append("")
    lines.append("| metric | A | B | Δ |")
    lines.append("|---|---|---|---|")
    a_metrics = {m["name"]: m for m in a["score"]["metrics"]}
    b_metrics = {m["name"]: m for m in b["score"]["metrics"]}
    names = sorted(set(a_metrics) | set(b_metrics))
    for n in names:
        ma, mb = a_metrics.get(n), b_metrics.get(n)
        av = ma["value"] if ma else "—"
        bv = mb["value"] if mb else "—"
        try:
            delta = f"{(mb['value'] - ma['value']):+.4f}"
        except (TypeError, KeyError):
            delta = ""
        lines.append(f"| {n} | {_fmt_metric(ma) if ma else '—'} | {_fmt_metric(mb) if mb else '—'} | {delta} |")
    lines.append("")
    lines.append("## state delta")
    state_keys = (
        "transcript_len", "tags_count", "builder_versions",
        "critic_reviews", "clarifications_resolved",
    )
    lines.append("| key | A | B |")
    lines.append("|---|---|---|")
    for k in state_keys:
        lines.append(f"| {k} | {a.get(k,0)} | {b.get(k,0)} |")
    cost_a = a["cost"]["estimated_cost_usd"]
    cost_b = b["cost"]["estimated_cost_usd"]
    lines.append(f"| cost_usd | {cost_a:.6f} | {cost_b:.6f} |")
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    a = _load(Path(args.a))
    b = _load(Path(args.b))
    print(render_diff(a, b))
    return 0


if __name__ == "__main__":
    sys.exit(main())
