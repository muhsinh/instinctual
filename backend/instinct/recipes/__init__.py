"""Recipe registry + classification routing.

Importing this module side-effect-imports every concrete recipe so they
self-register. Adding a new archetype: drop a `<archetype>.py` file that
imports `register` and registers a Recipe subclass at module level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..session import SessionState
from .base import (
    BuildPlan,
    CheckResult,
    Recipe,
    ValidationResult,
)

_REGISTRY: dict[str, Recipe] = {}


def register(recipe: Recipe) -> Recipe:
    if recipe.archetype in _REGISTRY:
        raise ValueError(f"recipe already registered: {recipe.archetype}")
    _REGISTRY[recipe.archetype] = recipe
    return recipe


def get(archetype: str) -> Recipe:
    if archetype not in _REGISTRY:
        raise KeyError(f"unknown archetype: {archetype}")
    return _REGISTRY[archetype]


def all_recipes() -> list[Recipe]:
    return list(_REGISTRY.values())


def archetypes() -> list[str]:
    return sorted(_REGISTRY)


@dataclass
class ClassificationResult:
    archetype: str
    confidence: float
    runner_up: Optional[str] = None
    runner_up_confidence: float = 0.0


def classify_heuristic(state: SessionState) -> ClassificationResult:
    """Phase-A stub classifier.

    Scans every registered recipe's heuristic_match_score() and picks the
    highest. Falls back to spec_doc when no recipe scores above the floor.
    The real LLM-driven classifier (Synthesis when API keys land) replaces
    this; both must produce ClassificationResult so call sites don't change.
    """
    FALLBACK_FLOOR = 0.15
    scored = sorted(
        ((r.archetype, r.heuristic_match_score(state)) for r in _REGISTRY.values()),
        key=lambda kv: kv[1],
        reverse=True,
    )
    if not scored:
        return ClassificationResult(archetype="spec_doc", confidence=0.0)
    top, top_score = scored[0]
    runner = scored[1] if len(scored) > 1 else None
    if top_score < FALLBACK_FLOOR:
        return ClassificationResult(
            archetype="spec_doc",
            confidence=0.0,
            runner_up=top,
            runner_up_confidence=top_score,
        )
    return ClassificationResult(
        archetype=top,
        confidence=top_score,
        runner_up=runner[0] if runner else None,
        runner_up_confidence=runner[1] if runner else 0.0,
    )


# --- Self-registering recipe imports (must come last to avoid circular). ---
# Each module registers its Recipe subclass at import time.
from . import scheduled_python_script as _spc  # noqa: F401, E402
from . import streamlit_dashboard as _sd  # noqa: F401, E402
from . import spec_doc as _sd_doc  # noqa: F401, E402

__all__ = [
    "BuildPlan",
    "CheckResult",
    "ClassificationResult",
    "Recipe",
    "ValidationResult",
    "all_recipes",
    "archetypes",
    "classify_heuristic",
    "get",
    "register",
]
