"""Shared session state read/written by every agent loop in an active meeting."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from .cost_tracker import CostTracker
from .ws_protocol import (
    Clarification,
    CriticReview,
    FinalSpec,
    ResolvedClarification,
    ScreenFrame,
    SpecDraft,
    Utterance,
    UtteranceTag,
    VisionObservation,
)


@dataclass
class SessionState:
    """All agent loops share one of these per active meeting.

    Mutating fields are guarded by their corresponding asyncio.Lock; signal
    fields (asyncio.Event) coordinate cross-loop wakeups so the orchestrator
    doesn't poll.
    """

    session_id: str
    started_at: float = field(default_factory=time.time)

    # Amendment 4: snapshotted once at session start, never updated mid-session.
    user_context: str = ""

    transcript: list[Utterance] = field(default_factory=list)
    tags: dict[str, UtteranceTag] = field(default_factory=dict)
    builder_versions: list[SpecDraft] = field(default_factory=list)
    critic_reviews: list[CriticReview] = field(default_factory=list)
    pending_clarification: Optional[Clarification] = None
    resolved_clarifications: list[ResolvedClarification] = field(default_factory=list)
    final_synthesis: Optional[FinalSpec] = None
    cost_tracker: CostTracker = field(default_factory=CostTracker)

    # v1 — Vision peer stream (parallel to transcript, not piped through Tagger).
    screen_frames: list[ScreenFrame] = field(default_factory=list)
    vision_observations: list[VisionObservation] = field(default_factory=list)

    # --- async coordination ---
    transcript_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    tags_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    builder_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    clarification_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    vision_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    new_utterance: asyncio.Event = field(default_factory=asyncio.Event)
    new_builder_version: asyncio.Event = field(default_factory=asyncio.Event)
    new_critic_review: asyncio.Event = field(default_factory=asyncio.Event)
    new_screen_frame: asyncio.Event = field(default_factory=asyncio.Event)
    new_vision_observation: asyncio.Event = field(default_factory=asyncio.Event)
    session_ended: asyncio.Event = field(default_factory=asyncio.Event)

    def latest_builder_version(self) -> Optional[SpecDraft]:
        return self.builder_versions[-1] if self.builder_versions else None

    def latest_critic_review(self) -> Optional[CriticReview]:
        return self.critic_reviews[-1] if self.critic_reviews else None
