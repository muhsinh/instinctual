"""Recipe interface (v1 Phase A).

Each recipe is a contract: archetype identity, classifier hint for Synthesis,
recipe-specific BuildPlan schema, Claude Code prompt template, validators,
and an optional deployer hint. Recipes are first-class code — version
controlled, evaluated, prompts iterated against eval scores. Adding a new
archetype is a new file in this package, not a core code change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Optional

from pydantic import BaseModel

from ..session import SessionState


class BuildPlan(BaseModel):
    """Recipe-specific build plan. Subclass per recipe with its own fields."""

    archetype: str


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class ValidationResult:
    archetype: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_dict(self) -> dict:
        return {
            "archetype": self.archetype,
            "passed": self.passed,
            "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.checks],
        }


class Recipe(ABC):
    """Abstract recipe. Subclass per archetype."""

    archetype: ClassVar[str]                       # unique key (e.g. "streamlit_dashboard")
    description: ClassVar[str]                     # human-readable, surfaced in classifier
    classifier_hint: ClassVar[str]                 # prompt fragment for Synthesis classifier
    build_plan_class: ClassVar[type[BuildPlan]]    # the recipe's BuildPlan subclass
    deployer: ClassVar[Optional[str]] = None       # adapter name (Phase C); None = local-only

    @abstractmethod
    def build_plan_from_state(self, state: SessionState) -> BuildPlan:
        """Construct the recipe's BuildPlan from accumulated session state.

        Phase A implementations may use simple heuristics. The real Builder
        agent (when API keys land) replaces these with LLM-driven extraction.
        """

    @abstractmethod
    def builder_prompt_template(self) -> str:
        """The Claude Code prompt template invoked to generate the artifact.

        Should reference {{build_plan}} and {{user_context}} placeholders.
        Receivers (a Claude subprocess driver, or the eval harness) substitute
        values before sending to the model.
        """

    @abstractmethod
    def validate_artifact(self, artifact_dir: Path) -> ValidationResult:
        """Smoke-test the generated artifact. Returns per-check results."""

    def heuristic_match_score(self, state: SessionState) -> float:
        """Cheap, deterministic 0..1 score for "does this archetype fit?".

        Used as a fallback when no LLM classifier is available (Phase A
        wire-check) and as a tiebreaker / sanity check alongside the real
        classifier later. Default returns 0; override per recipe.
        """
        return 0.0

    @classmethod
    def parse_build_plan(cls, raw: dict[str, Any]) -> BuildPlan:
        return cls.build_plan_class.model_validate(raw)
