"""Tests for v1 Phase A — recipes, classifier, validators, vision wiring."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from instinct.eval.fixture import load_fixture
from instinct.eval.replay import main as replay_main
from instinct.eval.score import load_summary
from instinct.recipes import all_recipes, archetypes, classify_heuristic, get
from instinct.recipes.scheduled_python_script import ScheduledPythonScriptBuildPlan
from instinct.recipes.spec_doc import SpecDocBuildPlan
from instinct.recipes.streamlit_dashboard import StreamlitDashboardBuildPlan
from instinct.session import SessionState
from instinct.ws_protocol import Utterance, VisionObservation


# --- Registry --------------------------------------------------------------


def test_three_recipes_registered():
    assert set(archetypes()) == {"scheduled_python_script", "streamlit_dashboard", "spec_doc"}
    assert len(all_recipes()) == 3


def test_get_returns_correct_recipe():
    assert get("scheduled_python_script").build_plan_class is ScheduledPythonScriptBuildPlan
    assert get("streamlit_dashboard").build_plan_class is StreamlitDashboardBuildPlan
    assert get("spec_doc").build_plan_class is SpecDocBuildPlan


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        get("nonexistent_archetype")


def test_double_registration_raises():
    from instinct.recipes import register
    from instinct.recipes.spec_doc import SpecDocRecipe
    with pytest.raises(ValueError):
        register(SpecDocRecipe())


# --- Heuristic classifier --------------------------------------------------


def test_classifier_picks_spec_doc_when_empty():
    s = SessionState(session_id="x")
    cr = classify_heuristic(s)
    assert cr.archetype == "spec_doc"


def test_classifier_picks_scheduled_on_cron_keywords():
    s = SessionState(session_id="x")
    s.transcript = [
        Utterance(id="u1", speaker="A", text="We need a script that runs every day at 9am.", timestamp_seconds=0.0),
        Utterance(id="u2", speaker="B", text="Right, a daily cron job to email the metrics.", timestamp_seconds=10.0),
    ]
    cr = classify_heuristic(s)
    assert cr.archetype == "scheduled_python_script"
    assert cr.confidence > 0.4


def test_classifier_picks_streamlit_on_dashboard_keywords():
    s = SessionState(session_id="x")
    s.transcript = [
        Utterance(id="u1", speaker="A", text="We want a dashboard with charts for the team.", timestamp_seconds=0.0),
        Utterance(id="u2", speaker="B", text="Streamlit is fine. Plot weekly active users.", timestamp_seconds=10.0),
    ]
    cr = classify_heuristic(s)
    assert cr.archetype == "streamlit_dashboard"


def test_vision_observations_boost_streamlit_classifier():
    """Vision is parallel context; a dashboard observation should pull
    classification toward streamlit_dashboard even when the text is ambiguous."""
    s = SessionState(session_id="x")
    s.transcript = [
        Utterance(id="u1", speaker="A", text="We should think about the metrics view.", timestamp_seconds=0.0),
    ]
    s.vision_observations = [
        VisionObservation(frame_id="f1", timestamp_seconds=10.0,
                          content_type="dashboard",
                          summary="existing analytics dashboard with line chart"),
    ]
    cr = classify_heuristic(s)
    assert cr.archetype == "streamlit_dashboard"


# --- Validators ------------------------------------------------------------


def test_streamlit_validator_passes_on_well_formed_artifact(tmp_path: Path):
    (tmp_path / "app.py").write_text("import streamlit as st\nst.title('x')\n")
    (tmp_path / "requirements.txt").write_text("streamlit\n")
    vr = get("streamlit_dashboard").validate_artifact(tmp_path)
    assert vr.passed
    names = {c.name for c in vr.checks}
    assert {"has_app_py", "imports_streamlit", "calls_st", "has_requirements_txt"}.issubset(names)


def test_streamlit_validator_fails_on_missing_app(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("streamlit\n")
    vr = get("streamlit_dashboard").validate_artifact(tmp_path)
    assert not vr.passed


def test_streamlit_validator_fails_on_syntax_error(tmp_path: Path):
    (tmp_path / "app.py").write_text("import streamlit as st\nst.title('x'\n")  # unterminated
    (tmp_path / "requirements.txt").write_text("streamlit\n")
    vr = get("streamlit_dashboard").validate_artifact(tmp_path)
    parses = next(c for c in vr.checks if c.name == "app_py:parses")
    assert not parses.passed


def test_scheduled_python_script_validator(tmp_path: Path):
    (tmp_path / "job.py").write_text(
        "def main():\n    print('hi')\n\nif __name__ == '__main__':\n    main()\n"
    )
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n")
    vr = get("scheduled_python_script").validate_artifact(tmp_path)
    assert vr.passed
    names = {c.name for c in vr.checks}
    assert "has_python_file" in names
    assert "requirements_well_formed" in names


def test_spec_doc_validator_requires_sections(tmp_path: Path):
    (tmp_path / "SPEC.md").write_text("# Hi\n\nDecisions\nOpen Questions\nNext Steps\n")
    vr = get("spec_doc").validate_artifact(tmp_path)
    assert vr.passed


# --- BuildPlan schemas roundtrip ------------------------------------------


def test_build_plan_schemas_roundtrip():
    """Each recipe's BuildPlan must serialize and re-validate via parse_build_plan."""
    for r in all_recipes():
        s = SessionState(session_id="x")
        plan = r.build_plan_from_state(s)
        raw = plan.model_dump(mode="json")
        re_parsed = r.parse_build_plan(raw)
        assert re_parsed.archetype == r.archetype


# --- End-to-end harness with v1 changes -----------------------------------


def test_replay_streamlit_fixture_classifies_correctly(tmp_path: Path):
    fixtures = Path(__file__).resolve().parent.parent / "eval" / "fixtures"
    rc = replay_main([
        str(fixtures / "streamlit_demo"),
        "--speed", "max",
        "--agents", "stub",
        "--output", str(tmp_path),
        "--quiet",
    ])
    # Decision precision/recall fail (stubs), but archetype_correct should pass.
    runs = list(tmp_path.glob("*/streamlit_demo"))
    assert runs
    summary = load_summary(runs[0])
    metric_by_name = {m["name"]: m for m in summary["score"]["metrics"]}
    assert "archetype_correct" in metric_by_name
    arch = metric_by_name["archetype_correct"]
    assert arch["passed"] is True, f"expected streamlit_dashboard, got {arch['detail']}"


# --- Vision wiring ---------------------------------------------------------


def test_stub_vision_in_orchestrator_is_safe():
    """Verify the orchestrator runs end-to-end with a StubVision included."""
    from instinct.orchestrator import session_loop, stub_agent_set
    from instinct.transcription import MockedTranscription

    async def main():
        utts = [Utterance(id=f"u{i}", speaker="A", text=f"hi {i}", timestamp_seconds=float(i)) for i in range(3)]
        state = SessionState(session_id="vt")
        agents = stub_agent_set()
        assert agents.vision is not None
        await session_loop(state, MockedTranscription(source=utts, speed="max"), agents)
        assert state.session_ended.is_set()

    asyncio.run(main())


def test_vision_agent_skip_unchanged_frames(tmp_path: Path):
    """Frame-delta heuristic should mark identical frames as unchanged.

    We don't make a live API call here — we exercise the skip path by
    feeding two identical frames and verifying the second produces an
    'unchanged' observation without ever invoking the client.
    """
    import asyncio
    from unittest.mock import AsyncMock

    from instinct.agents.vision import VisionAgent
    from instinct.ws_protocol import ScreenFrame

    client = AsyncMock()
    agent = VisionAgent(client=client, min_change_threshold=0.5)

    f = ScreenFrame(id="f1", timestamp_seconds=0.0, image_b64="ZmFrZQ==")  # "fake"
    state = SessionState(session_id="v")

    async def run():
        # Manually set the last-seen hash to f's hash so the delta path skips.
        import hashlib
        agent._last_seen_frame_hash = hashlib.sha1("ZmFrZQ==".encode()).hexdigest()
        obs = await agent._observe_frame(f, state)
        assert obs is not None
        assert obs.summary == "(unchanged)"
        client.call.assert_not_awaited()

    asyncio.run(run())
