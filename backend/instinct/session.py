"""Shared session state read/written by every agent loop in an active meeting.

v1 push: introduces ArtifactThread. A meeting can produce N independent
artifacts (script + dashboard + Linear epic, etc.); each lives in its own
thread with its own builder/critic/clarification loop. The transcript and
tags remain single-stream — Topic Tracker assigns each utterance to a thread
by appending utterance ids into ArtifactThread.utterance_ids.

Legacy single-track callers (existing tests + scorer_metrics) read aggregated
properties (`builder_versions`, `critic_reviews`, `final_synthesis`,
`pending_clarification`, `resolved_clarifications`) that flatten across all
threads. Single-thread fixtures continue to behave as before.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from .cost_tracker import CostTracker
from .ws_protocol import (
    Clarification,
    CriticReview,
    FeasibilityConcern,
    FinalSpec,
    ResolvedClarification,
    ScreenFrame,
    SpecDraft,
    TopicEvent,
    Utterance,
    UtteranceTag,
    VisionObservation,
)


@dataclass
class ArtifactThread:
    """One coherent build target within a session. Topic Tracker spawns
    these on detected pivots; Builder/Critic/Clarifier/Synthesis run a per-
    thread loop. Each thread carries its own version history."""

    id: str
    inferred_topic: str
    started_at_ts: float = field(default_factory=time.time)
    started_at_utterance_id: Optional[str] = None

    utterance_ids: list[str] = field(default_factory=list)

    builder_versions: list[SpecDraft] = field(default_factory=list)
    critic_reviews: list[CriticReview] = field(default_factory=list)
    pending_clarification: Optional[Clarification] = None
    resolved_clarifications: list[ResolvedClarification] = field(default_factory=list)

    archetype: Optional[str] = None
    archetype_confidence: float = 0.0
    build_plan: Optional[dict[str, Any]] = None
    final_spec: Optional[FinalSpec] = None

    feasibility: list[FeasibilityConcern] = field(default_factory=list)
    build_result: Optional[dict[str, Any]] = None      # populated by claude code subprocess
    deployment: Optional[dict[str, Any]] = None        # populated by deployers

    # Per-thread async signals.
    new_builder_version: asyncio.Event = field(default_factory=asyncio.Event)
    new_critic_review: asyncio.Event = field(default_factory=asyncio.Event)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


def _new_thread_id() -> str:
    return f"thread_{uuid.uuid4().hex[:12]}"


@dataclass
class SessionState:
    """All agent loops share one of these per active meeting."""

    session_id: str
    started_at: float = field(default_factory=time.time)

    # Amendment 4: snapshot once at session start, never updated mid-session.
    user_context: str = ""

    # Single transcript + tag stream.
    transcript: list[Utterance] = field(default_factory=list)
    tags: dict[str, UtteranceTag] = field(default_factory=dict)

    # Topic Tracker output stream.
    topic_events: list[TopicEvent] = field(default_factory=list)

    # Vision peer stream.
    screen_frames: list[ScreenFrame] = field(default_factory=list)
    vision_observations: list[VisionObservation] = field(default_factory=list)

    # v1: multiple artifact threads, each with its own version history.
    artifacts: list[ArtifactThread] = field(default_factory=list)

    # At-most-one active clarification across the whole session (UI invariant).
    # The pending_clarification on the owning thread points to this same object.
    active_clarification: Optional[Clarification] = None
    active_clarification_thread_id: Optional[str] = None
    pending_clarification_queue: list[tuple[str, Clarification]] = field(default_factory=list)

    # Optional calendar prime (#9).
    calendar_event: Optional[dict[str, Any]] = None

    # Mid-meeting steering notes.
    steering_notes: list[dict[str, Any]] = field(default_factory=list)

    # Post-meeting user refinements queued for re-synthesis.
    post_meeting_refinements: list[str] = field(default_factory=list)

    # Screen-sharing state hint from Mac.
    screen_sharing_active: bool = False

    cost_tracker: CostTracker = field(default_factory=CostTracker)

    # --- async coordination (transcript-level) ---
    transcript_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    tags_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    artifacts_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    clarification_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    vision_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    new_utterance: asyncio.Event = field(default_factory=asyncio.Event)
    new_topic_event: asyncio.Event = field(default_factory=asyncio.Event)
    new_artifact_thread: asyncio.Event = field(default_factory=asyncio.Event)
    new_screen_frame: asyncio.Event = field(default_factory=asyncio.Event)
    new_vision_observation: asyncio.Event = field(default_factory=asyncio.Event)
    new_steering_note: asyncio.Event = field(default_factory=asyncio.Event)
    session_ended: asyncio.Event = field(default_factory=asyncio.Event)

    # --- thread-graph helpers ---

    def thread_by_id(self, thread_id: str) -> Optional[ArtifactThread]:
        for t in self.artifacts:
            if t.id == thread_id:
                return t
        return None

    async def spawn_thread(
        self, *, inferred_topic: str, started_at_utterance_id: Optional[str] = None,
    ) -> ArtifactThread:
        thread = ArtifactThread(
            id=_new_thread_id(),
            inferred_topic=inferred_topic,
            started_at_utterance_id=started_at_utterance_id,
        )
        async with self.artifacts_lock:
            self.artifacts.append(thread)
        self.new_artifact_thread.set()
        return thread

    async def ensure_default_thread(self) -> ArtifactThread:
        """Single-thread fallback for fixtures without a Topic Tracker.

        Idempotent — returns the existing default thread if already created."""
        if self.artifacts:
            return self.artifacts[0]
        thread = await self.spawn_thread(inferred_topic="(default)")
        # Treat every utterance to-date as belonging to the default thread.
        async with self.transcript_lock:
            for u in self.transcript:
                thread.utterance_ids.append(u.id)
        return thread

    # --- aggregated views (legacy single-track callers) ---

    @property
    def builder_versions(self) -> list[SpecDraft]:
        out: list[SpecDraft] = []
        for t in self.artifacts:
            out.extend(t.builder_versions)
        return out

    @property
    def critic_reviews(self) -> list[CriticReview]:
        out: list[CriticReview] = []
        for t in self.artifacts:
            out.extend(t.critic_reviews)
        return out

    @property
    def pending_clarification(self) -> Optional[Clarification]:
        return self.active_clarification

    @property
    def resolved_clarifications(self) -> list[ResolvedClarification]:
        out: list[ResolvedClarification] = []
        for t in self.artifacts:
            out.extend(t.resolved_clarifications)
        return out

    @property
    def final_synthesis(self) -> Optional[FinalSpec]:
        """Returns the first thread's final_spec (legacy single-thread reads).

        Multi-thread callers should iterate `state.artifacts` directly."""
        for t in self.artifacts:
            if t.final_spec is not None:
                return t.final_spec
        return None

    def latest_builder_version(self) -> Optional[SpecDraft]:
        for t in self.artifacts:
            if t.builder_versions:
                return t.builder_versions[-1]
        return None

    def latest_critic_review(self) -> Optional[CriticReview]:
        for t in self.artifacts:
            if t.critic_reviews:
                return t.critic_reviews[-1]
        return None
