"""Vision agent (v1 Phase A).

Processes ScreenFrames at 1-2fps and emits VisionObservations into shared
SessionState as a peer to the transcript stream. Vision output is not
piped through the Tagger — it's a different modality. Builder consumes
both transcript-derived intent AND screen-derived visual context together.

Frame-delta heuristic: skip the API call when consecutive frames are
near-identical (cheap perceptual hash on bytes). Real perceptual diffing
(structural similarity, embeddings) is a v1 polish item; Phase A uses
length+SHA1 collision as a deterministic skip signal.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..anthropic_client import AnthropicCall, AnthropicClient, cache_breakpoint
from ..cost_tracker import CostTracker
from ..session import SessionState
from ..ws_protocol import ScreenFrame, VisionObservation

log = logging.getLogger(__name__)


VISION_MODEL = "claude-haiku-4-5"


_VISION_SYSTEM = """\
You are Instinct's Vision agent. You inspect a single screen frame from a live
meeting and report what's on screen. Output strict JSON, no prose.

JSON shape (all fields required, use null where unknown):
{
  "application_detected": "VS Code" | "Figma" | "Chrome" | ...,
  "content_type": "chart" | "code" | "doc" | "figma" | "dashboard" | "terminal" | "presentation" | "image" | "other" | "unknown",
  "extracted_text": "the most relevant text legible in the frame, max 500 chars" | null,
  "summary": "one-sentence description of what's on screen, terse"
}

Be terse. Skip pleasantries. Skip explanations. JSON only.
"""


@dataclass
class VisionAgent:
    """Real vision agent. Calls Claude with image input and a cached prefix."""

    name: str = "vision"
    client: Optional[AnthropicClient] = None
    capture_sink: Optional[Any] = None  # eval.capture.CaptureSink-shaped, optional
    min_change_threshold: float = 0.02   # below this, treat as identical and skip
    fixture_root: Optional[Path] = None  # fixture dir for resolving image_path

    _last_seen_frame_hash: Optional[str] = field(default=None, init=False)

    async def run(self, state: SessionState) -> None:
        """Watch for new frames; analyze and append observations."""
        if self.client is None:
            log.info("VisionAgent has no AnthropicClient; skipping (Phase-A path)")
            await state.session_ended.wait()
            return

        last_seen = 0
        while not state.session_ended.is_set():
            ended = asyncio.create_task(state.session_ended.wait())
            new_frame = asyncio.create_task(state.new_screen_frame.wait())
            done, pending = await asyncio.wait(
                {ended, new_frame}, return_when=asyncio.FIRST_COMPLETED
            )
            for t in pending:
                t.cancel()
            if state.session_ended.is_set():
                return

            async with state.vision_lock:
                new = state.screen_frames[last_seen:]
                last_seen = len(state.screen_frames)
            state.new_screen_frame.clear()

            for frame in new:
                obs = await self._observe_frame(frame, state)
                if obs is None:
                    continue
                async with state.vision_lock:
                    state.vision_observations.append(obs)
                state.new_vision_observation.set()

    async def _observe_frame(self, frame: ScreenFrame, state: SessionState) -> Optional[VisionObservation]:
        image_b64 = self._load_image_b64(frame)
        if image_b64 is None:
            log.warning("vision: no image data for frame %s", frame.id)
            return None

        # Frame-delta skip: cheap content-hash equality.
        h = hashlib.sha1(image_b64.encode("ascii")).hexdigest()
        change = 1.0 if h != self._last_seen_frame_hash else 0.0
        if change < self.min_change_threshold:
            log.debug("vision: skipping unchanged frame %s", frame.id)
            return VisionObservation(
                frame_id=frame.id,
                timestamp_seconds=frame.timestamp_seconds,
                visual_change_score=change,
                summary="(unchanged)",
            )
        self._last_seen_frame_hash = h

        media_type = "image/png"  # Mac app captures PNG; refined when Mac side ships.
        call = AnthropicCall(
            model=VISION_MODEL,
            system=[
                {"type": "text", "text": _VISION_SYSTEM, "cache_control": cache_breakpoint()},
                # User context fits inside the cached prefix (Amendment 4 from v0 plan).
                {"type": "text", "text": f"Team context:\n{state.user_context}", "cache_control": cache_breakpoint()},
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                        },
                        {"type": "text", "text": f"Frame timestamp {frame.timestamp_seconds:.1f}s. Report JSON only."},
                    ],
                }
            ],
            max_tokens=400,
        )

        t0 = time.monotonic()
        try:
            result = await self.client.call(call, cost_tracker=state.cost_tracker)
        except Exception:
            log.exception("vision call failed for frame %s", frame.id)
            return None
        latency_ms = (time.monotonic() - t0) * 1000.0

        if self.capture_sink is not None:
            try:
                self.capture_sink.record(
                    agent=self.name,
                    trigger=f"frame:{frame.id}",
                    prompt={"system_blocks": len(call.system), "model": call.model},
                    response={"text_len": len(result.text)},
                    usage=result.usage,
                    cost_usd=0.0,  # incremental cost lives in the cost_tracker snapshot
                    latency_ms=latency_ms,
                )
            except Exception:
                log.exception("vision capture sink record failed")

        parsed = _parse_vision_json(result.text)
        return VisionObservation(
            frame_id=frame.id,
            timestamp_seconds=frame.timestamp_seconds,
            application_detected=parsed.get("application_detected"),
            content_type=parsed.get("content_type", "unknown"),
            extracted_text=parsed.get("extracted_text"),
            visual_change_score=change,
            summary=parsed.get("summary", "")[:500],
        )

    def _load_image_b64(self, frame: ScreenFrame) -> Optional[str]:
        if frame.image_b64:
            return frame.image_b64
        if frame.image_path and self.fixture_root is not None:
            p = (self.fixture_root / frame.image_path).resolve()
            if p.exists():
                return base64.b64encode(p.read_bytes()).decode("ascii")
        return None


def _parse_vision_json(text: str) -> dict:
    import json
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Be lenient — strip code fences if the model wrapped it.
        cleaned = text.strip().lstrip("`").rstrip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {}


@dataclass
class StubVision:
    """Phase-A wire-check stub. Doesn't read frames or call Claude."""

    name: str = "vision"

    async def run(self, state: SessionState) -> None:
        await state.session_ended.wait()
