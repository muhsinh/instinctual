"""Tests for the eval harness wiring (Amendment 5 step 16)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from instinct.eval.capture import AGENT_NAMES, RunCapture, run_dir_for
from instinct.eval.fixture import load_fixture
from instinct.eval.replay import main as replay_main
from instinct.eval.score import load_summary
from instinct.eval.scorer_metrics import score_run, text_similarity
from instinct.orchestrator import session_loop, stub_agent_set
from instinct.session import SessionState
from instinct.transcription import MockedTranscription


PHASE1_FIXTURES = ("clean", "walked_back", "topic_shift")
ALL_FIXTURES = PHASE1_FIXTURES + ("streamlit_demo",)


@pytest.mark.parametrize("name", PHASE1_FIXTURES)
def test_fixtures_load_and_have_ground_truth(fixtures_dir: Path, name: str) -> None:
    fix = load_fixture(fixtures_dir / name)
    assert fix.name == name
    assert fix.utterances, f"{name} has no utterances"
    assert fix.ground_truth.decisions, f"{name} has no ground-truth decisions"
    bar = fix.metadata.bar
    assert 0.0 <= bar.decision_precision_min <= 1.0
    assert 0.0 <= bar.decision_recall_min <= 1.0
    assert bar.max_cost_usd > 0


def test_run_capture_creates_per_agent_files(tmp_path: Path) -> None:
    cap = RunCapture(run_dir=run_dir_for(tmp_path), fixture_name="x")
    files = {p.name for p in cap.fixture_dir.iterdir()}
    for agent in AGENT_NAMES:
        assert f"{agent}.jsonl" in files


@pytest.mark.parametrize("name", PHASE1_FIXTURES)
def test_score_run_against_empty_state_fails_bar(fixtures_dir: Path, name: str) -> None:
    """Wire-check: with no agent output, decision precision/recall are 0,
    so any fixture with a non-trivial bar fails. This proves the scorer is
    actually looking at agent output and not silently returning success."""
    fix = load_fixture(fixtures_dir / name)
    state = SessionState(session_id=f"empty-{name}")
    report = score_run(state, fix)
    assert report.passed is False
    metric_names = {m.name for m in report.metrics}
    assert {"decision_precision", "decision_recall", "cost_under_bar"}.issubset(metric_names)


async def _drive_stub_session(fixtures_dir: Path, name: str) -> SessionState:
    fix = load_fixture(fixtures_dir / name)
    state = SessionState(session_id=f"stub-{name}")
    transcription = MockedTranscription(source=list(fix.utterances), speed="max")
    await session_loop(state, transcription, stub_agent_set())
    return state


@pytest.mark.parametrize("name", PHASE1_FIXTURES)
async def test_session_loop_drains_transcript_with_stubs(fixtures_dir: Path, name: str) -> None:
    fix = load_fixture(fixtures_dir / name)
    state = await _drive_stub_session(fixtures_dir, name)
    assert len(state.transcript) == len(fix.utterances)
    assert state.session_ended.is_set()
    assert state.final_synthesis is not None  # stub synthesis fired


def test_text_similarity_basics() -> None:
    assert text_similarity("hello world", "hello world") == pytest.approx(1.0)
    assert text_similarity("hello world", "completely different stuff") == pytest.approx(0.0)
    assert 0.0 < text_similarity("ship on Friday", "we will ship friday") < 1.0


def test_replay_cli_writes_summary_and_exits_nonzero(tmp_path: Path, fixtures_dir: Path) -> None:
    """End-to-end CLI test: replay stubs, expect FAIL exit, valid summary written."""
    rc = replay_main([
        str(fixtures_dir / "clean"),
        "--speed", "max",
        "--agents", "stub",
        "--output", str(tmp_path),
        "--quiet",
    ])
    assert rc != 0  # stubs fail the bar
    # find the run dir we just produced
    runs = list(tmp_path.glob("*/clean"))
    assert runs, "no run dir created"
    summary = load_summary(runs[0])
    assert summary["fixture"] == "clean"
    assert summary["passed"] is False
    assert summary["transcript_len"] > 0
    assert summary["agents"] == "stub"
    # All five per-agent jsonls were touched
    files = {p.name for p in runs[0].iterdir()}
    for agent in AGENT_NAMES:
        assert f"{agent}.jsonl" in files
    assert "summary.json" in files
