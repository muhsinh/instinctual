"""Eval harness fixture schema + loader (Amendment 5).

A fixture is a directory containing `fixture.json`. Phase-2 will add
`audio.wav` alongside; the schema does not need to change for that.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from ..ws_protocol import ScreenFrame, Utterance


class FixtureBar(BaseModel):
    """Per-fixture pass/fail criteria. Different fixtures can demand
    different bars (clean fixture tighter than adversarial)."""

    decision_precision_min: float = 0.7
    decision_recall_min: float = 0.7
    max_cost_usd: float = 3.0
    expected_clarifications_fired_min: int = 0


class FixtureMetadata(BaseModel):
    duration_seconds: int
    speakers: list[str]
    description: str
    bar: FixtureBar
    # v1 Phase A: optional expected archetype. Scorer compares against the
    # classifier output (heuristic for Phase A; LLM-driven once Synthesis lands).
    expected_archetype: str | None = None


class GroundTruthDecision(BaseModel):
    text: str
    source_utterance_ids: list[str] = Field(default_factory=list)


class GroundTruthOpenQuestion(BaseModel):
    text: str
    blocking: bool = False


class FixtureGroundTruth(BaseModel):
    decisions: list[GroundTruthDecision] = Field(default_factory=list)
    open_questions: list[GroundTruthOpenQuestion] = Field(default_factory=list)
    expected_clarifications_fired_min: int = 0
    topic_shifts_at_seconds: list[int] = Field(default_factory=list)


class Fixture(BaseModel):
    name: str
    metadata: FixtureMetadata
    utterances: list[Utterance]
    ground_truth: FixtureGroundTruth
    # v1 Phase A: optional screen frames for Vision agent. Frames may either
    # carry inline image_b64 or reference image_path relative to fixture dir.
    frames: list[ScreenFrame] = Field(default_factory=list)


def load_fixture(path: str | Path) -> Fixture:
    """Accept either a directory containing fixture.json, or the file itself."""
    p = Path(path)
    if p.is_dir():
        p = p / "fixture.json"
    if not p.exists():
        raise FileNotFoundError(f"fixture not found: {p}")
    return Fixture.model_validate_json(p.read_text(encoding="utf-8"))


def write_fixture(directory: str | Path, fixture: Fixture) -> Path:
    """Write a fixture to <dir>/fixture.json. Used by tests/fixture authors."""
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    target = d / "fixture.json"
    target.write_text(
        json.dumps(fixture.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return target
