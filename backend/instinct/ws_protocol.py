"""WebSocket message types and shared agent-output schemas.

Pydantic models used for both wire framing (app <-> backend) and as the
canonical in-memory representations referenced by SessionState.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


# Agent intent labels (Tagger output).
IntentLabel = Literal[
    "decision",
    "proposal",
    "brainstorm",
    "aside",
    "question",
    "walked_back",
    "context",
]


class Utterance(BaseModel):
    """One transcript line. Append-only on SessionState.transcript.

    `text` is the raw transcript output (what agents read for quality).
    `redacted_text` is PII-stripped with session-consistent pseudonyms (what
    the corpus writer persists). When None, no redaction has run.
    """

    id: str
    speaker: str
    text: str
    timestamp_seconds: float
    redacted_text: Optional[str] = None


class UtteranceTag(BaseModel):
    """Tagger output for a single utterance."""

    utterance_id: str
    speaker: str
    intent: IntentLabel
    confidence: float
    topic: str
    references_prior: Optional[str] = None


class SpecRequirement(BaseModel):
    id: str
    text: str
    confidence: float
    source_utterances: list[str] = Field(default_factory=list)


class SpecOpenQuestion(BaseModel):
    id: str
    text: str
    blocking: bool = False
    source_utterances: list[str] = Field(default_factory=list)


class SpecDecision(BaseModel):
    id: str
    text: str
    source_utterances: list[str] = Field(default_factory=list)


class SpecDraft(BaseModel):
    """Builder output. SessionState retains the full version history."""

    version: int
    title: str
    summary: str
    requirements: list[SpecRequirement] = Field(default_factory=list)
    open_questions: list[SpecOpenQuestion] = Field(default_factory=list)
    decisions_made: list[SpecDecision] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    confidence_overall: float = 0.0


class CriticConcern(BaseModel):
    type: Literal[
        "feasibility",
        "scope_creep",
        "contradiction",
        "unstated_assumption",
        "missing_requirement",
    ]
    severity: Literal["blocker", "warning", "nit"]
    text: str
    suggested_clarification: Optional[str] = None


class CriticReview(BaseModel):
    reviewing_version: int
    concerns: list[CriticConcern] = Field(default_factory=list)


class Clarification(BaseModel):
    """A pending one-tap question for the user."""

    id: str
    question: str
    options: list[str]
    fallback_if_ignored: str
    created_at: float


class ResolvedClarification(BaseModel):
    id: str
    question: str
    options: list[str]
    outcome: str  # selected option text, or fallback text if timed out
    timed_out: bool


class FinalSpec(BaseModel):
    """Synthesis output.

    v1: Synthesis classifies the meeting outcome to a recipe and produces a
    recipe-specific BuildPlan. The base FinalSpec fields stay populated for
    every archetype (they're useful even when the artifact is code), and
    `archetype` + `build_plan` carry the archetype-specific structured data.
    """

    final_spec_markdown: str
    executive_summary: str
    decisions_made: list[str]
    open_questions: list[str]
    assumptions_inferred: list[str]
    suggested_next_steps: list[str]
    confidence_notes: str

    # v1 additions (Phase A — Recipe layer):
    archetype: str = "spec_doc"
    archetype_confidence: float = 0.0
    build_plan: Optional[dict[str, Any]] = None  # recipe-specific; recipe parses it


class ScreenFrame(BaseModel):
    """One captured screen frame, uploaded by the Mac app via WebSocket.

    v1 Phase A defines the type; the live capture/upload path lands when the
    Mac app gets ScreenCapture.swift in Phase 3 of the original v0 plan
    (or under the v1 phase plan, whichever ships first).
    """

    id: str
    timestamp_seconds: float
    image_b64: Optional[str] = None  # base64 PNG/JPEG; absent in fixtures-only mode
    image_path: Optional[str] = None  # relative path under the fixture dir
    width: int = 0
    height: int = 0


class VisionObservation(BaseModel):
    """Vision agent output for a single frame (v1 spec)."""

    frame_id: str
    timestamp_seconds: float
    application_detected: Optional[str] = None  # "VS Code" / "Figma" / "Chrome" / etc.
    content_type: Literal[
        "chart",
        "code",
        "doc",
        "figma",
        "dashboard",
        "terminal",
        "presentation",
        "image",
        "other",
        "unknown",
    ] = "unknown"
    extracted_text: Optional[str] = None
    visual_change_score: float = 0.0  # 0..1 — how different from prior frame
    summary: str = ""


class TopicEvent(BaseModel):
    """Topic Tracker output per utterance (v1 push spec)."""

    utterance_id: str
    kind: Literal["continues", "revisits", "pivots"]
    confidence: float
    target_thread_id: str  # for continues/revisits, existing id; for pivots, new id
    inferred_topic: Optional[str] = None  # populated on pivots
    timestamp_seconds: float = 0.0


class FeasibilityConcern(BaseModel):
    """Output from feasibility checks against external services."""

    service: str            # "linear" | "stripe" | "github" | "slack" | etc.
    reachable: bool
    issue: Optional[str] = None
    suggested_alternatives: list[str] = Field(default_factory=list)
    thread_id: Optional[str] = None


class BuildResult(BaseModel):
    """Output from the Claude Code subprocess driver."""

    archetype: str
    thread_id: str
    output_dir: str
    files_generated: list[str] = Field(default_factory=list)
    validation_passed: bool = False
    validation_detail: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    mode: Literal["mock", "live", "fallback_qwen"] = "mock"
    error: Optional[str] = None


class DeploymentResult(BaseModel):
    """Output from a deployment adapter."""

    deployer: str
    thread_id: str
    success: bool
    url: Optional[str] = None
    detail: dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


# --- WebSocket messages --------------------------------------------------

# Inbound: app -> backend


class WSSessionStart(BaseModel):
    type: Literal["session_start"] = "session_start"
    session_id: str


class WSAudioChunk(BaseModel):
    type: Literal["audio_chunk"] = "audio_chunk"
    data: str  # base64-encoded PCM16 mono 16kHz
    timestamp: float


class WSClarificationResponse(BaseModel):
    type: Literal["clarification_response"] = "clarification_response"
    clarification_id: str
    selected_option: str


class WSSessionEnd(BaseModel):
    type: Literal["session_end"] = "session_end"


class WSScreenSharingState(BaseModel):
    """Mac signals when the user is/isn't actively screen-sharing. Vision
    pipeline can throttle frame intake when sharing is off."""

    type: Literal["screen_sharing_state"] = "screen_sharing_state"
    active: bool


class WSSteeringNote(BaseModel):
    """User mid-meeting note that biases agents toward / away from a direction.
    Optionally targeted at a specific thread (e.g., 'use Postgres not Mongo
    for the dashboard')."""

    type: Literal["steering_note"] = "steering_note"
    text: str
    target_thread_id: Optional[str] = None


class WSPostMeetingRefinement(BaseModel):
    """User-supplied corrections after the meeting ended; triggers re-synthesis."""

    type: Literal["post_meeting_refinement"] = "post_meeting_refinement"
    text: str


class WSCalendarEvent(BaseModel):
    """Mac sends Calendar.app metadata at session start so agents prime on it."""

    type: Literal["calendar_event"] = "calendar_event"
    event: dict[str, Any]  # {title, start, end, attendees: [{email,name}], description, location}


InboundMessage = Annotated[
    Union[
        WSSessionStart,
        WSAudioChunk,
        WSClarificationResponse,
        WSSessionEnd,
        WSScreenSharingState,
        WSSteeringNote,
        WSPostMeetingRefinement,
        WSCalendarEvent,
    ],
    Field(discriminator="type"),
]


# Outbound: backend -> app


class WSTranscriptUpdate(BaseModel):
    type: Literal["transcript_update"] = "transcript_update"
    utterance: Utterance


class WSSpecUpdate(BaseModel):
    type: Literal["spec_update"] = "spec_update"
    version: int
    spec: SpecDraft
    diff: Optional[dict[str, Any]] = None  # JSON merge-patch style; populated when known
    thread_id: Optional[str] = None  # v1 — per-ArtifactThread targeting


class WSClarificationPending(BaseModel):
    type: Literal["clarification_pending"] = "clarification_pending"
    clarification: Clarification


class WSClarificationResolved(BaseModel):
    type: Literal["clarification_resolved"] = "clarification_resolved"
    clarification_id: str
    outcome: str
    timed_out: bool


class WSCostUpdate(BaseModel):
    type: Literal["cost_update"] = "cost_update"
    current_usd: float


class WSSynthesisComplete(BaseModel):
    type: Literal["synthesis_complete"] = "synthesis_complete"
    final_spec: FinalSpec


class WSError(BaseModel):
    type: Literal["error"] = "error"
    message: str


class WSThreadSpawned(BaseModel):
    type: Literal["thread_spawned"] = "thread_spawned"
    thread_id: str
    inferred_topic: str
    started_at_utterance_id: Optional[str] = None


class WSFeasibilityBlocker(BaseModel):
    type: Literal["feasibility_blocker"] = "feasibility_blocker"
    service: str
    issue: str
    thread_id: Optional[str] = None
    suggested_alternatives: list[str] = Field(default_factory=list)


class WSDeploymentComplete(BaseModel):
    type: Literal["deployment_complete"] = "deployment_complete"
    thread_id: str
    url: str
    deployer: str
    success: bool = True


OutboundMessage = Annotated[
    Union[
        WSTranscriptUpdate,
        WSSpecUpdate,
        WSClarificationPending,
        WSClarificationResolved,
        WSCostUpdate,
        WSSynthesisComplete,
        WSError,
        WSThreadSpawned,
        WSFeasibilityBlocker,
        WSDeploymentComplete,
    ],
    Field(discriminator="type"),
]
