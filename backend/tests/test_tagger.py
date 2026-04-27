"""Tests for v1 NVIDIA-backed Tagger.

Live API integration is exercised by the harness against fixtures; these
tests use a mock NvidiaClient to nail the parsing/wiring logic.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass

import pytest

from instinct.agents.tagger import Tagger, _parse_tagger_json
from instinct.providers.nvidia import ChatResult
from instinct.session import SessionState
from instinct.ws_protocol import Utterance


@dataclass
class _MockNvidiaClient:
    """Returns a fixed ChatResult per call. Round-robins through `responses`."""

    responses: list[str]
    _i: int = 0

    async def chat(self, **kwargs):
        text = self.responses[self._i % len(self.responses)]
        self._i += 1
        return ChatResult(text=text, usage={"prompt_tokens": 10, "completion_tokens": 5}, finish_reason="stop")


def test_parse_well_formed_json():
    out = _parse_tagger_json('{"intent":"decision","confidence":0.9,"topic":"x","references_prior":null}')
    assert out is not None and out["intent"] == "decision"


def test_parse_with_code_fences():
    raw = '```json\n{"intent":"proposal","confidence":0.7,"topic":"y","references_prior":null}\n```'
    out = _parse_tagger_json(raw)
    assert out is not None and out["intent"] == "proposal"


def test_parse_falls_back_to_brace_extraction():
    raw = "Sure! Here's the JSON: {\"intent\":\"question\",\"confidence\":0.5,\"topic\":\"z\",\"references_prior\":null} hope that helps"
    out = _parse_tagger_json(raw)
    assert out is not None and out["intent"] == "question"


def test_parse_returns_none_on_garbage():
    assert _parse_tagger_json("not json at all") is None


async def test_tagger_handles_three_utterances():
    """End-to-end-ish: drive the Tagger directly over a small synthetic
    transcript with a mock client. Verify all three tags land in state.tags
    with correct utterance ids."""
    state = SessionState(session_id="t1")
    state.transcript = [
        Utterance(id="t_u01", speaker="A", text="Let's roll back the auth change.", timestamp_seconds=0.0),
        Utterance(id="t_u02", speaker="B", text="Sounds good.", timestamp_seconds=10.0),
        Utterance(id="t_u03", speaker="A", text="Should we open a regression test?", timestamp_seconds=20.0),
    ]

    client = _MockNvidiaClient(responses=[
        '{"intent":"proposal","confidence":0.9,"topic":"roll back auth","references_prior":null}',
        '{"intent":"decision","confidence":0.85,"topic":"agree to roll back","references_prior":"t_u01"}',
        '{"intent":"question","confidence":0.8,"topic":"regression test","references_prior":"t_u01"}',
    ])
    tagger = Tagger(client=client)

    # Pre-populate session as if transcript_consumer already drained, then end.
    state.session_ended.set()
    await tagger.run(state)

    assert len(state.tags) == 3
    assert state.tags["t_u01"].intent == "proposal"
    assert state.tags["t_u02"].intent == "decision"
    assert state.tags["t_u03"].intent == "question"
    assert state.tags["t_u02"].references_prior == "t_u01"


async def test_tagger_skips_when_cost_paused():
    state = SessionState(session_id="t2")
    state.transcript = [Utterance(id="t_u01", speaker="A", text="hi", timestamp_seconds=0.0)]
    state.cost_tracker.paused = True
    state.session_ended.set()

    client = _MockNvidiaClient(responses=['{"intent":"context","confidence":0.5,"topic":"x","references_prior":null}'])
    tagger = Tagger(client=client)
    await tagger.run(state)

    assert len(state.tags) == 0  # cost-paused → no tags written


async def test_tagger_handles_malformed_response_gracefully():
    state = SessionState(session_id="t3")
    state.transcript = [Utterance(id="t_u01", speaker="A", text="hi", timestamp_seconds=0.0)]
    state.session_ended.set()

    client = _MockNvidiaClient(responses=["this is not json"])
    tagger = Tagger(client=client)
    # Should not raise.
    await tagger.run(state)
    # Tag should NOT be written when parsing fails.
    assert len(state.tags) == 0
