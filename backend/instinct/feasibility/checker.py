"""Feasibility Checker (v1 push, #5).

Inspects each ArtifactThread's BuildPlan + utterances for references to
external services. For known services, probes reachability. For obviously-
fake service names, flags as infeasible immediately. Failed probes emit a
FeasibilityConcern into the thread; if a Clarifier is wired, the concern
becomes a one-tap clarification surfaced via the HUD.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Iterable, Optional

from ..session import ArtifactThread, SessionState
from ..ws_protocol import FeasibilityConcern
from .service_registry import Service, default_registry, detect_obviously_infeasible

log = logging.getLogger(__name__)


@dataclass
class FeasibilityChecker:
    services: dict[str, Service] = field(default_factory=default_registry)

    async def check_session(self, state: SessionState) -> list[FeasibilityConcern]:
        all_concerns: list[FeasibilityConcern] = []
        for thread in state.artifacts:
            concerns = await self.check_thread(thread, state)
            if concerns:
                async with thread.lock:
                    thread.feasibility.extend(concerns)
                all_concerns.extend(concerns)
        return all_concerns

    async def check_thread(self, thread: ArtifactThread, state: SessionState) -> list[FeasibilityConcern]:
        text = self._gather_text(thread, state)
        concerns: list[FeasibilityConcern] = []

        # Pass 1: obvious-fake patterns. These trump real probes.
        for fake in detect_obviously_infeasible(text):
            concerns.append(FeasibilityConcern(
                service=fake,
                reachable=False,
                issue=f"'{fake}' does not appear to be a real, reachable service.",
                suggested_alternatives=["Specify the actual API name", "Use a documented service"],
                thread_id=thread.id,
            ))

        # Pass 2: registered services.
        text_lc = text.lower()
        seen_services: set[str] = set()
        for key, svc in self.services.items():
            if any(kw.lower() in text_lc for kw in svc.keywords) and key not in seen_services:
                seen_services.add(key)
                ok = await svc.is_reachable()
                if not ok:
                    concerns.append(FeasibilityConcern(
                        service=svc.display_name,
                        reachable=False,
                        issue=f"{svc.display_name} probe failed (status endpoint unreachable).",
                        suggested_alternatives=svc.suggested_alternatives,
                        thread_id=thread.id,
                    ))
                else:
                    concerns.append(FeasibilityConcern(
                        service=svc.display_name,
                        reachable=True,
                        thread_id=thread.id,
                    ))
        return concerns

    @staticmethod
    def _gather_text(thread: ArtifactThread, state: SessionState) -> str:
        parts: list[str] = []
        thread_utt_ids = set(thread.utterance_ids)
        for u in state.transcript:
            if u.id in thread_utt_ids:
                parts.append(u.text)
        if thread.build_plan:
            parts.append(json.dumps(thread.build_plan))
        if thread.final_spec is not None:
            parts.append(thread.final_spec.final_spec_markdown or "")
        return "\n".join(parts)


def blockers(concerns: Iterable[FeasibilityConcern]) -> list[FeasibilityConcern]:
    """Filter to only the unreachable ones (the ones a HUD should surface)."""
    return [c for c in concerns if not c.reachable]
