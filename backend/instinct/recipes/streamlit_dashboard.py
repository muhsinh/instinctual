"""streamlit_dashboard archetype — new in v1 Phase A.

Use case: meeting concludes with "we need a dashboard that shows X". The team
may have referenced an existing dashboard on screen (Vision agent's frames).
Output is a single Streamlit app file plus requirements.txt. Deploys via
Modal or Railway in Phase C.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..session import SessionState
from . import register
from .base import BuildPlan, CheckResult, Recipe, ValidationResult


_KEYWORDS = (
    "dashboard", "streamlit", "chart", "visualization", "viz", "metrics view",
    "graph", "plot", "kpi", "panel", "report ui", "interactive view",
)
_VISION_HINTS = ("dashboard", "chart")


class DataSource(BaseModel):
    name: str
    kind: Literal["postgres", "bigquery", "snowflake", "csv", "rest_api", "parquet", "other"]
    connection_hint: str = ""  # env var name, file path, etc.


class ChartSpec(BaseModel):
    title: str
    chart_type: Literal["line", "bar", "area", "pie", "table", "metric", "scatter", "heatmap", "other"]
    x: str = ""
    y: str = ""
    aggregation: str = ""  # sum/avg/count/etc.


class FilterSpec(BaseModel):
    name: str
    kind: Literal["date_range", "select", "multiselect", "slider", "text"]
    options: list[str] = Field(default_factory=list)


class VisualReference(BaseModel):
    """A screen frame the team referenced. Vision agent populated."""

    frame_id: str
    summary: str  # e.g., "the existing analytics dashboard with line chart of MAU"


class StreamlitDashboardBuildPlan(BuildPlan):
    archetype: str = "streamlit_dashboard"
    title: str
    description: str
    data_sources: list[DataSource] = Field(default_factory=list)
    charts: list[ChartSpec] = Field(default_factory=list)
    filters: list[FilterSpec] = Field(default_factory=list)
    references: list[VisualReference] = Field(default_factory=list)
    layout: Literal["sidebar", "tabs", "single_page"] = "single_page"


_BUILDER_TEMPLATE = """\
You are generating a Streamlit dashboard.

Build plan:
{{build_plan}}

Visual references the team showed during the meeting (use these to inform
layout and feel of the dashboard):
{{build_plan.references}}

User context:
{{user_context}}

Constraints:
- Single file: app.py using `import streamlit as st`.
- requirements.txt with streamlit and any libs implied by data_sources.
- Configure layout per build_plan.layout. If "sidebar", filters live in st.sidebar.
- Each chart in build_plan.charts gets a section header + the chart. Use plotly
  or st.line_chart/bar_chart per chart_type.
- Read secrets via st.secrets or env vars; never hardcode.
- The app must `import` cleanly with no runtime errors when no data is wired
  (i.e., it should render empty states, not crash).

Output the files. Then stop.
"""


class StreamlitDashboardRecipe(Recipe):
    archetype = "streamlit_dashboard"
    description = (
        "A Streamlit dashboard that visualizes one or more data sources with "
        "filters, charts, and an optional sidebar. Good for KPIs, metrics, "
        "interactive exploration."
    )
    classifier_hint = (
        "Pick this when the team agreed to build something visual + interactive: "
        "charts, filters, dashboard. Strong signal: someone said 'dashboard' or "
        "named a chart type, or pointed at an existing dashboard on screen."
    )
    build_plan_class = StreamlitDashboardBuildPlan
    deployer = "modal"

    def heuristic_match_score(self, state: SessionState) -> float:
        text = " ".join(u.text.lower() for u in state.transcript)
        if not text:
            transcript_score = 0.0
        else:
            hits = sum(1 for k in _KEYWORDS if k in text)
            transcript_score = min(1.0, 0.20 + 0.25 * hits)

        # Vision boost: if any observation flagged a chart/dashboard on screen,
        # bias toward this recipe.
        vision_score = 0.0
        for obs in state.vision_observations:
            if obs.content_type in _VISION_HINTS:
                vision_score = max(vision_score, 0.25)
            if any(h in (obs.summary or "").lower() for h in _VISION_HINTS):
                vision_score = max(vision_score, 0.35)
        return min(1.0, transcript_score + vision_score)

    def build_plan_from_state(self, state: SessionState) -> StreamlitDashboardBuildPlan:
        # Phase-A stub: real Builder fills via LLM. Provide a placeholder that
        # exercises every field so validators have something to chew on.
        refs = [
            VisualReference(frame_id=f.id, summary="(stub)")
            for f in state.screen_frames[:3]
        ]
        return StreamlitDashboardBuildPlan(
            title="(Phase-A stub dashboard)",
            description="(Phase-A stub — real Builder agent will populate)",
            references=refs,
        )

    def builder_prompt_template(self) -> str:
        return _BUILDER_TEMPLATE

    def validate_artifact(self, artifact_dir: Path) -> ValidationResult:
        checks: list[CheckResult] = []
        app_py = artifact_dir / "app.py"
        checks.append(CheckResult("has_app_py", passed=app_py.exists(), detail=str(app_py)))
        if app_py.exists():
            src = app_py.read_text(encoding="utf-8", errors="replace")
            try:
                ast.parse(src, filename=str(app_py))
                checks.append(CheckResult("app_py:parses", passed=True))
            except SyntaxError as e:
                checks.append(CheckResult("app_py:parses", passed=False, detail=str(e)))
            checks.append(CheckResult(
                "imports_streamlit",
                passed=bool(re.search(r"^\s*import\s+streamlit", src, re.MULTILINE)),
                detail="`import streamlit` present" if "import streamlit" in src else "missing",
            ))
            checks.append(CheckResult(
                "calls_st",
                passed="st." in src,
                detail="uses st.* somewhere" if "st." in src else "no st.* calls",
            ))
        req = artifact_dir / "requirements.txt"
        checks.append(CheckResult("has_requirements_txt", passed=req.exists(), detail=str(req)))
        if req.exists():
            content = req.read_text(encoding="utf-8")
            checks.append(CheckResult(
                "requirements_includes_streamlit",
                passed="streamlit" in content.lower(),
                detail="streamlit listed" if "streamlit" in content.lower() else "missing",
            ))
        return ValidationResult(archetype=self.archetype, checks=checks)


register(StreamlitDashboardRecipe())
