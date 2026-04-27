"""FastAPI server with the /session WebSocket endpoint.

Phase 1 ships the message dispatch and session registry; live audio routing
and end-to-end agent wire-up land in Phase 2/3 once the Mac app is talking
to the backend. The eval harness drives the orchestrator directly, so this
server isn't on the hot path for Phase-1 testing.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import TypeAdapter, ValidationError

from .session import SessionState
from .ws_protocol import (
    InboundMessage,
    OutboundMessage,
    WSAudioChunk,
    WSClarificationResponse,
    WSCostUpdate,
    WSError,
    WSSessionEnd,
    WSSessionStart,
)

log = logging.getLogger(__name__)


@dataclass
class ActiveSession:
    state: SessionState
    outbound: asyncio.Queue = field(default_factory=asyncio.Queue)
    loop_task: Optional[asyncio.Task] = None


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, ActiveSession] = {}

    def add(self, session_id: str, sess: ActiveSession) -> None:
        if session_id in self._sessions:
            raise RuntimeError(f"session {session_id} already exists")
        self._sessions[session_id] = sess

    def get(self, session_id: str) -> Optional[ActiveSession]:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> Optional[ActiveSession]:
        return self._sessions.pop(session_id, None)

    @property
    def count(self) -> int:
        return len(self._sessions)


app = FastAPI(title="instinct")
registry = SessionRegistry()
_inbound_adapter: TypeAdapter[InboundMessage] = TypeAdapter(InboundMessage)


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "active_sessions": registry.count}


@app.websocket("/session")
async def session_ws(ws: WebSocket) -> None:
    await ws.accept()
    sess: Optional[ActiveSession] = None
    forwarder: Optional[asyncio.Task] = None
    try:
        while True:
            try:
                raw = await ws.receive_json()
            except WebSocketDisconnect:
                break

            try:
                msg = _inbound_adapter.validate_python(raw)
            except ValidationError as e:
                await _send(ws, WSError(message=f"invalid message: {e.errors()[:1]}"))
                continue

            if isinstance(msg, WSSessionStart):
                if sess is not None:
                    await _send(ws, WSError(message="session already started on this socket"))
                    continue
                sess = ActiveSession(state=SessionState(session_id=msg.session_id))
                registry.add(msg.session_id, sess)
                forwarder = asyncio.create_task(_forward_outbound(ws, sess))
                # Phase-2/3: start session_loop with real transcription + agents.
                # Phase-1 leaves it un-started; harness drives orchestrator directly.

            elif isinstance(msg, WSAudioChunk):
                if sess is None:
                    await _send(ws, WSError(message="audio_chunk before session_start"))
                    continue
                # Phase-2: forward to sess.transcription.feed_audio(...)
                # Phase-1: noop.

            elif isinstance(msg, WSClarificationResponse):
                if sess is None:
                    await _send(ws, WSError(message="clarification_response before session_start"))
                    continue
                async with sess.state.clarification_lock:
                    pending = sess.state.pending_clarification
                    if pending is None or pending.id != msg.clarification_id:
                        await _send(ws, WSError(message="no matching pending clarification"))
                        continue
                    # Resolution + appending to resolved_clarifications happens in
                    # the Clarifier loop once it's wired up. Phase-1 placeholder
                    # just acknowledges receipt.

            elif isinstance(msg, WSSessionEnd):
                if sess is not None:
                    sess.state.session_ended.set()
                    if sess.loop_task is not None:
                        try:
                            await sess.loop_task
                        except Exception:
                            log.exception("session_loop terminated with error")
                break

    finally:
        if forwarder is not None:
            forwarder.cancel()
        if sess is not None:
            registry.remove(sess.state.session_id)
        try:
            await ws.close()
        except Exception:
            pass


async def _forward_outbound(ws: WebSocket, sess: ActiveSession) -> None:
    """Drains sess.outbound and ships messages to the connected client."""
    try:
        while True:
            msg: OutboundMessage = await sess.outbound.get()
            await _send(ws, msg)
            # Heartbeat the cost counter alongside any other outbound update.
            if not isinstance(msg, WSCostUpdate):
                await _send(
                    ws,
                    WSCostUpdate(current_usd=sess.state.cost_tracker.estimated_cost_usd()),
                )
    except asyncio.CancelledError:
        return


async def _send(ws: WebSocket, msg) -> None:
    """Send a Pydantic message as JSON. Tolerates closed sockets."""
    try:
        await ws.send_json(msg.model_dump())
    except Exception:
        log.debug("ws send failed (likely disconnected): %s", msg.__class__.__name__)
