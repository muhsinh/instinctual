"""Scoring metrics for replay runs (Amendment 5).

Primary metric: precision and recall on decision extraction. Secondary:
open-question recall, clarification-fire rate, cost vs the per-fixture bar.

The matching is intentionally simple in v0 — token-overlap (Jaccard) above a
threshold counts as a match. Exact-string match is too brittle. A semantic
match via embeddings or a structured-match LLM call is a future upgrade
plugged in via the same `text_similarity` seam.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from ..recipes import classify_heuristic
from ..session import SessionState
from .fixture import Fixture


# Jaccard threshold above which two texts count as the "same" decision.
# Tuned empirically; revisit during Phase 1 fixture authoring.
DEFAULT_MATCH_THRESHOLD = 0.4


def _word_set(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def text_similarity(a: str, b: str) -> float:
    """Jaccard over normalized word sets. 0..1."""
    aw, bw = _word_set(a), _word_set(b)
    if not aw or not bw:
        return 0.0
    return len(aw & bw) / len(aw | bw)


def _match_pairs(
    predicted: list[str], truth: list[str], threshold: float
) -> tuple[set[int], set[int]]:
    """Greedy 1:1 match by best similarity per prediction. Returns matched indices."""
    matched_p: set[int] = set()
    matched_t: set[int] = set()
    for i, p in enumerate(predicted):
        best_j, best_sim = -1, 0.0
        for j, t in enumerate(truth):
            if j in matched_t:
                continue
            sim = text_similarity(p, t)
            if sim > best_sim:
                best_sim, best_j = sim, j
        if best_sim >= threshold and best_j >= 0:
            matched_p.add(i)
            matched_t.add(best_j)
    return matched_p, matched_t


@dataclass
class MetricResult:
    name: str
    value: float
    threshold: float | None = None
    passed: bool | None = None
    detail: dict = field(default_factory=dict)


@dataclass
class ScoreReport:
    fixture_name: str
    metrics: list[MetricResult]
    total_cost_usd: float
    max_cost_usd: float

    @property
    def passed(self) -> bool:
        return all(m.passed is not False for m in self.metrics)

    def to_dict(self) -> dict:
        return {
            "fixture_name": self.fixture_name,
            "passed": self.passed,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "max_cost_usd": self.max_cost_usd,
            "metrics": [
                {
                    "name": m.name,
                    "value": round(m.value, 4),
                    "threshold": m.threshold,
                    "passed": m.passed,
                    **({"detail": m.detail} if m.detail else {}),
                }
                for m in self.metrics
            ],
        }


def _decision_texts(items: Iterable) -> list[str]:
    """Pull .text from list of objects (works for SpecDecision and GroundTruthDecision)."""
    return [getattr(it, "text", str(it)) for it in items]


def score_run(state: SessionState, fixture: Fixture, *, threshold: float = DEFAULT_MATCH_THRESHOLD) -> ScoreReport:
    """Score one replay run against fixture.ground_truth + fixture.metadata.bar."""
    bar = fixture.metadata.bar
    metrics: list[MetricResult] = []

    # Decisions: take from final_synthesis if available, else latest builder version.
    if state.final_synthesis is not None:
        predicted_decisions = list(state.final_synthesis.decisions_made)
    elif state.builder_versions:
        predicted_decisions = _decision_texts(state.builder_versions[-1].decisions_made)
    else:
        predicted_decisions = []
    truth_decisions = _decision_texts(fixture.ground_truth.decisions)

    matched_p, matched_t = _match_pairs(predicted_decisions, truth_decisions, threshold)
    precision = len(matched_p) / len(predicted_decisions) if predicted_decisions else 0.0
    recall = len(matched_t) / len(truth_decisions) if truth_decisions else 1.0  # vacuous

    metrics.append(MetricResult(
        name="decision_precision",
        value=precision,
        threshold=bar.decision_precision_min,
        passed=precision >= bar.decision_precision_min,
        detail={"predicted": len(predicted_decisions), "matched": len(matched_p)},
    ))
    metrics.append(MetricResult(
        name="decision_recall",
        value=recall,
        threshold=bar.decision_recall_min,
        passed=recall >= bar.decision_recall_min,
        detail={"truth": len(truth_decisions), "matched": len(matched_t)},
    ))

    # Open-question recall (informational, not gated unless we add a bar).
    if state.final_synthesis is not None:
        predicted_oq = list(state.final_synthesis.open_questions)
    elif state.builder_versions:
        predicted_oq = [oq.text for oq in state.builder_versions[-1].open_questions]
    else:
        predicted_oq = []
    truth_oq = [oq.text for oq in fixture.ground_truth.open_questions]
    if truth_oq:
        _, oq_matched = _match_pairs(predicted_oq, truth_oq, threshold)
        oq_recall = len(oq_matched) / len(truth_oq)
    else:
        oq_recall = 1.0
    metrics.append(MetricResult(
        name="open_question_recall",
        value=oq_recall,
        detail={"truth": len(truth_oq), "matched": len(predicted_oq) and len(_match_pairs(predicted_oq, truth_oq, threshold)[1])},
    ))

    # Clarifications fired vs minimum expected.
    fired = len(state.resolved_clarifications) + (1 if state.pending_clarification else 0)
    expected_min = max(
        bar.expected_clarifications_fired_min,
        fixture.ground_truth.expected_clarifications_fired_min,
    )
    metrics.append(MetricResult(
        name="clarifications_fired",
        value=float(fired),
        threshold=float(expected_min),
        passed=fired >= expected_min,
        detail={"fired": fired, "min_expected": expected_min},
    ))

    # Cost vs bar.
    total_cost = state.cost_tracker.estimated_cost_usd()
    metrics.append(MetricResult(
        name="cost_under_bar",
        value=total_cost,
        threshold=bar.max_cost_usd,
        passed=total_cost <= bar.max_cost_usd,
        detail={"cost_usd": total_cost, "bar_usd": bar.max_cost_usd},
    ))

    # v1 — archetype classification. Only gates the run if fixture declares an
    # expected_archetype. Uses synthesis output if available, else falls back
    # to the heuristic classifier (Phase-A path).
    expected_arch = fixture.metadata.expected_archetype
    if state.final_synthesis is not None and state.final_synthesis.archetype:
        chosen_arch = state.final_synthesis.archetype
        chosen_conf = state.final_synthesis.archetype_confidence
        chosen_via = "synthesis"
    else:
        cr = classify_heuristic(state)
        chosen_arch = cr.archetype
        chosen_conf = cr.confidence
        chosen_via = "heuristic"

    if expected_arch is not None:
        metrics.append(MetricResult(
            name="archetype_correct",
            value=1.0 if chosen_arch == expected_arch else 0.0,
            threshold=1.0,
            passed=chosen_arch == expected_arch,
            detail={
                "expected": expected_arch,
                "chosen": chosen_arch,
                "confidence": chosen_conf,
                "classifier": chosen_via,
            },
        ))
    else:
        metrics.append(MetricResult(
            name="archetype_chosen",
            value=chosen_conf,
            detail={"chosen": chosen_arch, "classifier": chosen_via},
        ))

    return ScoreReport(
        fixture_name=fixture.name,
        metrics=metrics,
        total_cost_usd=total_cost,
        max_cost_usd=bar.max_cost_usd,
    )
