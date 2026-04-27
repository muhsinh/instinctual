"""Transcription stream interface + Phase-1 mock.

Real Deepgram client lands in Phase 2 implementing the same `TranscriptionStream`
contract so the orchestrator + harness don't notice the swap.
"""

from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Iterable

from .ws_protocol import Utterance


# Speed accepts: "1x", "10x", "max", or any "<n>x" with n a positive number.
_SPEED_RE = re.compile(r"^(?P<n>\d+(?:\.\d+)?)x$")


def parse_speed(speed: str) -> float | None:
    """Returns the divisor: real-gap-seconds / divisor = sleep-seconds.
    None means "no sleep" (max speed).
    """
    if speed == "max":
        return None
    m = _SPEED_RE.match(speed)
    if m is None:
        raise ValueError(f"unknown speed {speed!r}; use 1x, 10x, max, or <n>x")
    n = float(m.group("n"))
    if n <= 0:
        raise ValueError(f"speed must be positive, got {speed!r}")
    return n


class TranscriptionStream(ABC):
    @abstractmethod
    def utterances(self) -> AsyncIterator[Utterance]:
        """Async generator yielding utterances as they arrive."""

    async def feed_audio(self, pcm_bytes: bytes, timestamp: float) -> None:  # noqa: B027
        """Optional. Mock ignores audio; Phase-2 Deepgram client overrides."""
        return None


@dataclass
class MockedTranscription(TranscriptionStream):
    """Drives a list of utterances at a configurable speed.

    1x replays in ~real time using each utterance's timestamp_seconds gap.
    10x replays at 10x speed. "max" emits with no inter-utterance delay.
    """

    source: list[Utterance]
    speed: str = "10x"

    def utterances(self) -> AsyncIterator[Utterance]:
        return self._iter()

    async def _iter(self) -> AsyncIterator[Utterance]:
        divisor = parse_speed(self.speed)
        prev_ts = 0.0
        for u in self.source:
            gap = max(0.0, u.timestamp_seconds - prev_ts)
            if divisor is not None and gap > 0:
                await asyncio.sleep(gap / divisor)
            yield u
            prev_ts = u.timestamp_seconds

    @classmethod
    def from_dicts(cls, items: Iterable[dict], *, speed: str = "10x") -> "MockedTranscription":
        return cls(source=[Utterance.model_validate(item) for item in items], speed=speed)
