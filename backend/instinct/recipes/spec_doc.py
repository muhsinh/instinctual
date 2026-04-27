"""spec_doc archetype — fallback when no other recipe matches.

This is the v0 default: produce a structured markdown spec document. The
classifier picks this when nothing else has a confident heuristic/LLM match.
No deployer; the artifact is read-only.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from ..session import SessionState
from . import register
from .base import BuildPlan, CheckResult, Recipe, ValidationResult


class SpecDocBuildPlan(BuildPlan):
    archetype: str = "spec_doc"
    title: str
    summary: str
    decisions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    final_markdown: str = ""


_BUILDER_TEMPLATE = """\
You are producing a markdown spec document that summarizes a meeting outcome.

Build plan:
{{build_plan}}

User context:
{{user_context}}

Output a single SPEC.md with these sections in order:
1. # {{build_plan.title}}
2. Executive Summary (2-3 sentences)
3. Decisions (one bullet per decision)
4. Open Questions (one bullet per question; mark blockers)
5. Next Steps (numbered list, owners if known)
6. Assumptions (what we inferred but didn't confirm)

Keep it concise. No preamble, no marketing, no apologies.
"""


class SpecDocRecipe(Recipe):
    archetype = "spec_doc"
    description = (
        "Markdown spec document fallback when the meeting outcome doesn't fit "
        "a code archetype. Always available; selected when nothing else scores."
    )
    classifier_hint = (
        "Default fallback. Pick this when the meeting was discussion or planning "
        "without a clear concrete artifact (no script, no dashboard, no ticket)."
    )
    build_plan_class = SpecDocBuildPlan
    deployer = None

    def heuristic_match_score(self, state: SessionState) -> float:
        # Always available as a low-floor fallback. If the transcript exists at
        # all, this archetype is a candidate — other recipes have to beat it on
        # heuristic strength to displace it.
        return 0.10 if state.transcript else 0.0

    def build_plan_from_state(self, state: SessionState) -> SpecDocBuildPlan:
        latest = state.builder_versions[-1] if state.builder_versions else None
        decisions = [d.text for d in latest.decisions_made] if latest else []
        oqs = [q.text for q in latest.open_questions] if latest else []
        return SpecDocBuildPlan(
            title=(latest.title if latest else "Meeting outcome"),
            summary=(latest.summary if latest else ""),
            decisions=decisions,
            open_questions=oqs,
            next_steps=[],
            final_markdown="",
        )

    def builder_prompt_template(self) -> str:
        return _BUILDER_TEMPLATE

    def validate_artifact(self, artifact_dir: Path) -> ValidationResult:
        checks: list[CheckResult] = []
        spec = artifact_dir / "SPEC.md"
        checks.append(CheckResult("has_spec_md", passed=spec.exists(), detail=str(spec)))
        if spec.exists():
            content = spec.read_text(encoding="utf-8")
            checks.append(CheckResult(
                "non_empty",
                passed=len(content.strip()) > 0,
                detail=f"{len(content)} chars",
            ))
            for required in ("Decisions", "Open Questions", "Next Steps"):
                checks.append(CheckResult(
                    f"has_{required.lower().replace(' ', '_')}",
                    passed=required in content,
                    detail=f"section present" if required in content else "section missing",
                ))
        return ValidationResult(archetype=self.archetype, checks=checks)


register(SpecDocRecipe())
