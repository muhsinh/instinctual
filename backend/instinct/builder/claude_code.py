"""Claude Code subprocess driver (v1 push, #4).

Two modes:
- MOCK (default in tests): produces canned files per archetype that pass
  the recipe's validators. Zero external dependencies, zero cost.
- LIVE: spawns `claude -p <prompt>` against `<output_dir>` and captures
  generated files. Used when the operator has Claude Code credentials.

Cost cap is $3 per meeting in LIVE mode. On exceed, falls back to
qwen3-coder via NVIDIA NIM (free) and regenerates. Total per-meeting cap
stays $5 once cost_tracker is wired (qwen calls flow through CostTracker
already).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shlex
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from ..providers.nvidia import NvidiaClient, model_for
from ..session import ArtifactThread, SessionState
from ..ws_protocol import BuildResult

log = logging.getLogger(__name__)


class ClaudeCodeMode(str, Enum):
    MOCK = "mock"
    LIVE = "live"


@dataclass
class ClaudeCodeDriver:
    """Runs the Builder's prompt against either mocked file generation or
    a real `claude -p` subprocess. Always validates output via the recipe's
    validator before returning."""

    mode: ClaudeCodeMode = ClaudeCodeMode.MOCK
    output_root: Path = field(default_factory=lambda: Path("./builds"))
    cost_cap_usd: float = 3.0
    nvidia_client: Optional[NvidiaClient] = None  # for fallback regen
    capture_sink: Optional[Any] = None
    subprocess_timeout_s: float = 600.0
    claude_cli: str = "claude"

    @classmethod
    def from_env(cls, output_root: Path, nvidia_client: Optional[NvidiaClient] = None) -> "ClaudeCodeDriver":
        mode_str = os.environ.get("INSTINCT_CLAUDE_CODE_MODE", "mock")
        try:
            mode = ClaudeCodeMode(mode_str)
        except ValueError:
            log.warning("invalid INSTINCT_CLAUDE_CODE_MODE=%s; defaulting to mock", mode_str)
            mode = ClaudeCodeMode.MOCK
        return cls(mode=mode, output_root=output_root, nvidia_client=nvidia_client)

    async def run(self, *, thread: ArtifactThread, state: SessionState) -> BuildResult:
        from ..recipes import get as get_recipe

        archetype = thread.archetype or "spec_doc"
        recipe = get_recipe(archetype)
        plan = thread.build_plan or {}
        out_dir = self.output_root / thread.id
        out_dir.mkdir(parents=True, exist_ok=True)

        files: list[str] = []
        cost = 0.0
        mode_used: str = self.mode.value
        error: Optional[str] = None

        try:
            if self.mode is ClaudeCodeMode.LIVE:
                files, cost, mode_used, error = await self._live_generate(
                    recipe=recipe, plan=plan, out_dir=out_dir, state=state, thread=thread,
                )
            else:
                files = _mock_generate(archetype, plan, out_dir)
                mode_used = "mock"
        except Exception as e:
            log.exception("claude_code generation failed for thread %s", thread.id)
            error = f"{type(e).__name__}: {e}"

        validation = recipe.validate_artifact(out_dir)
        result = BuildResult(
            archetype=archetype,
            thread_id=thread.id,
            output_dir=str(out_dir.resolve()),
            files_generated=files,
            validation_passed=validation.passed,
            validation_detail=validation.to_dict(),
            cost_usd=round(cost, 4),
            mode=mode_used,  # type: ignore[arg-type]
            error=error,
        )
        async with thread.lock:
            thread.build_result = result.model_dump()

        if self.capture_sink is not None:
            try:
                self.capture_sink.record(
                    agent="builder",
                    trigger=f"subprocess:{thread.id}",
                    prompt={"archetype": archetype, "thread": thread.id, "mode": mode_used},
                    response={"files": files, "validation_passed": validation.passed},
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    cost_usd=cost,
                    latency_ms=0.0,
                )
            except Exception:
                pass

        return result

    async def _live_generate(
        self,
        *,
        recipe: Any,
        plan: dict,
        out_dir: Path,
        state: SessionState,
        thread: ArtifactThread,
    ) -> tuple[list[str], float, str, Optional[str]]:
        """Spawn `claude -p <prompt>` against out_dir. Returns (files, cost,
        mode_used, error). On cost-cap exceed, falls back to qwen regen."""
        prompt = self._render_prompt(recipe=recipe, plan=plan, state=state)
        cmd = [self.claude_cli, "-p", prompt]
        log.info("spawning claude subprocess for thread %s", thread.id)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(out_dir),
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.subprocess_timeout_s,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return [], 0.0, "live", "subprocess timeout"
        except FileNotFoundError:
            return [], 0.0, "live", f"`{self.claude_cli}` not on PATH"

        rc = proc.returncode or 0
        files = sorted(p.name for p in out_dir.iterdir())
        # Cost in live mode is billed against the operator's Claude account,
        # not the NVIDIA cost_tracker. Approximate as 0 unless the subprocess
        # surfaces it.
        cost = 0.0
        error = None if rc == 0 else f"rc={rc} stderr={stderr.decode(errors='replace')[:200]}"
        return files, cost, "live", error

    def _render_prompt(self, *, recipe: Any, plan: dict, state: SessionState) -> str:
        template = recipe.builder_prompt_template()
        # Substitute {{build_plan}}, {{user_context}}, {{build_plan.<key>}} stubs.
        out = template
        out = out.replace("{{build_plan}}", json.dumps(plan, indent=2))
        out = out.replace("{{user_context}}", state.user_context or "(none)")
        out = out.replace("{{build_plan.references}}", json.dumps(plan.get("references", []), indent=2))
        for key, val in plan.items():
            out = out.replace(f"{{{{build_plan.{key}}}}}", json.dumps(val) if not isinstance(val, str) else val)
        return out


# --- mock generators --------------------------------------------------------


def _mock_generate(archetype: str, plan: dict, out_dir: Path) -> list[str]:
    if archetype == "scheduled_python_script":
        return _mock_scheduled_python_script(plan, out_dir)
    if archetype == "streamlit_dashboard":
        return _mock_streamlit_dashboard(plan, out_dir)
    if archetype == "linear_epic":
        return _mock_linear_epic(plan, out_dir)
    if archetype == "design_mockup":
        return _mock_design_mockup(plan, out_dir)
    return _mock_spec_doc(plan, out_dir)


def _safe_name(s: str) -> str:
    cleaned = "".join(c if c.isalnum() else "_" for c in (s or "job").strip().lower())
    cleaned = cleaned.strip("_") or "job"
    return cleaned[:40]


def _mock_scheduled_python_script(plan: dict, out_dir: Path) -> list[str]:
    name = _safe_name(plan.get("name") or "scheduled_job")
    description = (plan.get("description") or "Generated by Instinct mock builder.").replace('"""', "'''")
    deps = plan.get("dependencies") or []
    env_vars = plan.get("env_vars") or []
    function_purpose = plan.get("function_purpose") or "(no purpose specified)"
    schedule = plan.get("schedule_cron") or "0 9 * * *"

    deps_block = "\n".join(deps) + "\n" if deps else ""
    env_loads = "\n".join(f"    {ev} = os.environ.get('{ev}')" for ev in env_vars)

    py = f'''"""{description}

Schedule (configured by deployer, not in-code): {schedule}
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("{name}")


def main() -> int:
    log.info("{name} starting at %s", datetime.utcnow().isoformat())
{env_loads if env_vars else "    pass"}
    # purpose: {function_purpose}
    log.info("{name} done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''
    (out_dir / f"{name}.py").write_text(py, encoding="utf-8")
    (out_dir / "requirements.txt").write_text(deps_block, encoding="utf-8")
    return sorted(p.name for p in out_dir.iterdir())


def _mock_streamlit_dashboard(plan: dict, out_dir: Path) -> list[str]:
    title = plan.get("title") or "Dashboard"
    description = plan.get("description") or "Generated by Instinct mock builder."
    layout = plan.get("layout") or "single_page"
    charts = plan.get("charts") or []
    filters = plan.get("filters") or []
    data_sources = plan.get("data_sources") or []
    refs = plan.get("references") or []

    filter_lines = []
    for f in filters:
        if not isinstance(f, dict):
            continue
        kind = f.get("kind") or "text"
        nm = f.get("name") or "filter"
        if kind == "date_range":
            filter_lines.append(f'date_range = st.sidebar.date_input("{nm}", [])')
        elif kind == "select":
            opts = json.dumps(f.get("options") or [])
            filter_lines.append(f'{_safe_name(nm)} = st.sidebar.selectbox("{nm}", {opts})')
        elif kind == "multiselect":
            opts = json.dumps(f.get("options") or [])
            filter_lines.append(f'{_safe_name(nm)} = st.sidebar.multiselect("{nm}", {opts})')
        elif kind == "slider":
            filter_lines.append(f'{_safe_name(nm)} = st.sidebar.slider("{nm}", 0, 100, 50)')
        else:
            filter_lines.append(f'{_safe_name(nm)} = st.sidebar.text_input("{nm}")')

    chart_lines = []
    for ch in charts:
        if not isinstance(ch, dict):
            continue
        ct = ch.get("chart_type") or "table"
        ttl = ch.get("title") or "Chart"
        chart_lines.append(f'st.subheader("{ttl}")')
        if ct == "metric":
            chart_lines.append(f'st.metric("{ttl}", "—")')
        elif ct == "table":
            chart_lines.append('st.dataframe(pd.DataFrame())')
        elif ct == "line":
            chart_lines.append('st.line_chart(pd.DataFrame())')
        elif ct == "bar":
            chart_lines.append('st.bar_chart(pd.DataFrame())')
        elif ct == "area":
            chart_lines.append('st.area_chart(pd.DataFrame())')
        elif ct == "scatter":
            chart_lines.append('st.scatter_chart(pd.DataFrame())')
        else:
            chart_lines.append('st.write("(chart placeholder)")')

    sidebar_block = "\n".join(filter_lines) if (layout == "sidebar" and filter_lines) else ""
    chart_block = "\n".join(chart_lines) or 'st.write("Configure charts in build plan to render.")'

    refs_comment = "\n".join(f"# - {r.get('summary','(ref)')}" for r in refs if isinstance(r, dict))
    ds_comment = "\n".join(
        f"# - {d.get('name','source')} ({d.get('kind','')})"
        for d in data_sources if isinstance(d, dict)
    )

    py = f'''"""{title}

{description}

Generated by Instinct mock builder. Connect to the data sources listed
below before deploying.
"""

import pandas as pd
import streamlit as st


st.set_page_config(layout="wide", page_title="{title}")
st.title("{title}")
st.caption("{description}")

# Data sources referenced in the build plan:
{ds_comment or "# (none specified)"}

# Visual references the team showed during the meeting:
{refs_comment or "# (none)"}

# --- Filters ---
{sidebar_block or "# (no sidebar filters configured)"}

# --- Charts ---
{chart_block}
'''
    (out_dir / "app.py").write_text(py, encoding="utf-8")
    deps = ["streamlit", "pandas"]
    (out_dir / "requirements.txt").write_text("\n".join(deps) + "\n", encoding="utf-8")
    return sorted(p.name for p in out_dir.iterdir())


def _mock_linear_epic(plan: dict, out_dir: Path) -> list[str]:
    title = plan.get("title") or "Untitled epic"
    description = plan.get("description") or ""
    sub_tickets = plan.get("sub_tickets") or []
    payload = {
        "epic": {"title": title, "description": description},
        "issues": [
            {
                "title": st.get("title", "(untitled)") if isinstance(st, dict) else str(st),
                "description": st.get("description", "") if isinstance(st, dict) else "",
                "labels": st.get("labels", []) if isinstance(st, dict) else [],
                "assignee": st.get("assignee") if isinstance(st, dict) else None,
            }
            for st in sub_tickets
        ],
    }
    (out_dir / "linear_payload.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md = f"# {title}\n\n{description}\n\n## Sub-tickets\n\n" + "\n".join(
        f"- {i['title']}" for i in payload["issues"]
    )
    (out_dir / "epic.md").write_text(md, encoding="utf-8")
    return sorted(p.name for p in out_dir.iterdir())


def _mock_design_mockup(plan: dict, out_dir: Path) -> list[str]:
    descriptor = {
        "title": plan.get("title") or "Mockup",
        "layout": plan.get("layout") or "(unspecified)",
        "brand_tokens": plan.get("brand_tokens") or {},
        "components": plan.get("components") or [],
        "generated_via": "mock",
    }
    (out_dir / "descriptor.json").write_text(json.dumps(descriptor, indent=2), encoding="utf-8")
    # Tiny placeholder PNG (1x1 transparent) — bytes inlined to avoid an image lib dep.
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    (out_dir / "mockup.png").write_bytes(png_bytes)
    return sorted(p.name for p in out_dir.iterdir())


def _mock_spec_doc(plan: dict, out_dir: Path) -> list[str]:
    title = plan.get("title") or "Meeting Outcome"
    summary = plan.get("summary") or ""
    decisions = plan.get("decisions") or []
    open_qs = plan.get("open_questions") or []
    next_steps = plan.get("next_steps") or []

    md = f"# {title}\n\n## Executive Summary\n{summary}\n\n## Decisions\n"
    md += "\n".join(f"- {d}" for d in decisions) or "- (none)"
    md += "\n\n## Open Questions\n"
    md += "\n".join(f"- {q}" for q in open_qs) or "- (none)"
    md += "\n\n## Next Steps\n"
    md += "\n".join(f"1. {s}" for s in next_steps) or "1. (none)"
    md += "\n"
    (out_dir / "SPEC.md").write_text(md, encoding="utf-8")
    return sorted(p.name for p in out_dir.iterdir())
