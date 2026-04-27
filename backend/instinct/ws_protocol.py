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
    """One transcript line. Append-only on SessionState.transcript."""

    id: str
    speaker: str
    text: str
    timestamp_seconds: float


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


InboundMessage = Annotated[
    Union[WSSessionStart, WSAudioChunk, WSClarificationResponse, WSSessionEnd],
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


OutboundMessage = Annotated[
    Union[
        WSTranscriptUpdate,
        WSSpecUpdate,
        WSClarificationPending,
        WSClarificationResolved,
        WSCostUpdate,
        WSSynthesisComplete,
        WSError,
    ],
    Field(discriminator="type"),
]
