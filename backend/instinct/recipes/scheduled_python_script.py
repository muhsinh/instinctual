"""scheduled_python_script archetype — the v0 archetype, ported as a Recipe.

Use case: meeting concludes with "we should have a script that runs on a schedule
and does X" — typical examples are daily metrics emails, weekly reports, cron
data-syncs. Output is a single Python file plus requirements.txt; deploys via
the Modal adapter (Phase C).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from pydantic import Field

from ..session import SessionState
from . import register
from .base import BuildPlan, CheckResult, Recipe, ValidationResult


_KEYWORDS = (
    "schedule", "scheduled", "every day", "daily", "weekly", "monthly", "cron",
    "run every", "automated job", "background job", "cronjob", "hourly",
    "fires every", "kicks off", "kicks every",
)


class ScheduledPythonScriptBuildPlan(BuildPlan):
    archetype: str = "scheduled_python_script"
    name: str = Field(..., description="Snake-case filename, e.g. daily_metrics_email")
    description: str
    schedule_cron: str = Field(..., description="Standard 5-field cron, e.g. '0 9 * * *'")
    function_purpose: str
    inputs: list[str] = Field(default_factory=list, description="APIs / data sources")
    outputs: list[str] = Field(default_factory=list, description="email / file / db row / etc.")
    dependencies: list[str] = Field(default_factory=list, description="pip packages")
    env_vars: list[str] = Field(default_factory=list, description="REQUIRED_SECRET_NAMES")


_BUILDER_TEMPLATE = """\
You are generating a single Python file that runs on a schedule.

Build plan:
{{build_plan}}

User context (background you should respect):
{{user_context}}

Constraints:
- Single file: {{build_plan.name}}.py with a `main()` entry point.
- requirements.txt listing exactly the dependencies in build_plan.dependencies.
- Use only environment variables named in build_plan.env_vars for secrets.
- The schedule itself is configured by the deployer (Modal); do NOT include
  cron/sleep loops in the script.
- Do log start/end timestamps and any errors to stdout.
- No interactive prompts; the script must run unattended.

Output the files. Then stop.
"""


class ScheduledPythonScriptRecipe(Recipe):
    archetype = "scheduled_python_script"
    description = (
        "A scheduled Python script that runs on a cadence (cron). Good for daily "
        "reports, periodic data syncs, alerting jobs. Single file + requirements.txt."
    )
    classifier_hint = (
        "Pick this when the team agreed they want something that runs automatically "
        "on a schedule (daily/weekly/cron). Distinguishing signal: someone said "
        "'every day' or 'on a schedule' or named a cron-like cadence."
    )
    build_plan_class = ScheduledPythonScriptBuildPlan
    deployer = "modal"

    def heuristic_match_score(self, state: SessionState) -> float:
        text = " ".join(u.text.lower() for u in state.transcript)
        if not text:
            return 0.0
        hits = sum(1 for k in _KEYWORDS if k in text)
        # Saturate around 3+ keyword hits.
        return min(1.0, 0.25 + 0.25 * hits)

    def build_plan_from_state(self, state: SessionState) -> ScheduledPythonScriptBuildPlan:
        # Phase-A stub: real builder agent fills these via LLM extraction.
        # Provide a deterministic placeholder so eval harness can exercise the path.
        return ScheduledPythonScriptBuildPlan(
            name="placeholder_job",
            description="(Phase-A stub — real Builder agent will populate)",
            schedule_cron="0 9 * * *",
            function_purpose="(stub)",
        )

    def builder_prompt_template(self) -> str:
        return _BUILDER_TEMPLATE

    def validate_artifact(self, artifact_dir: Path) -> ValidationResult:
        checks: list[CheckResult] = []
        py_files = list(artifact_dir.glob("*.py"))
        checks.append(CheckResult(
            "has_python_file",
            passed=bool(py_files),
            detail=f"{len(py_files)} .py file(s)" if py_files else "none",
        ))
        for p in py_files:
            src = p.read_text(encoding="utf-8", errors="replace")
            try:
                tree = ast.parse(src, filename=str(p))
                has_main = any(
                    isinstance(n, ast.FunctionDef) and n.name == "main" for n in tree.body
                )
                checks.append(CheckResult(
                    f"{p.name}:parses",
                    passed=True,
                    detail="ast.parse ok",
                ))
                checks.append(CheckResult(
                    f"{p.name}:has_main",
                    passed=has_main,
                    detail="found main() entry point" if has_main else "no main() defined",
                ))
            except SyntaxError as e:
                checks.append(CheckResult(
                    f"{p.name}:parses",
                    passed=False,
                    detail=f"SyntaxError: {e}",
                ))
        req = artifact_dir / "requirements.txt"
        checks.append(CheckResult(
            "has_requirements_txt",
            passed=req.exists(),
            detail=str(req),
        ))
        if req.exists():
            for line in req.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                ok = bool(re.match(r"^[A-Za-z0-9._\-]+(?:[<>=!~]=?[A-Za-z0-9._*\-+]+)?$", line))
                if not ok:
                    checks.append(CheckResult(
                        "requirements_well_formed",
                        passed=False,
                        detail=f"unparseable line: {line!r}",
                    ))
                    break
            else:
                checks.append(CheckResult("requirements_well_formed", passed=True))
        return ValidationResult(archetype=self.archetype, checks=checks)


register(ScheduledPythonScriptRecipe())
