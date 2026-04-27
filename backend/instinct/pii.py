"""PII redaction (v1 foundation).

Primary backend: NVIDIA's nvidia/gliner-pii NER model. Because the exact API
shape for that model can shift, we attempt the live call and degrade
gracefully to a regex-based fallback. Both backends produce the same
RedactedResult shape, so callers don't branch.

Every utterance flows through `redact()` before being written anywhere
durable (sidecar, corpus). The original text stays in SessionState for the
agents to operate on; only the redacted variant escapes into persistent
storage.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .providers.nvidia import NvidiaClient, model_for

log = logging.getLogger(__name__)


# Order matters — apply the more specific patterns first so e.g. an email
# isn't partially substituted by the username regex.
_REGEX_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("PHONE", re.compile(r"\b(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("URL", re.compile(r"https?://\S+")),
    ("IP", re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")),
]


@dataclass
class PIIEntity:
    type: str           # EMAIL / PHONE / PERSON / ORG / etc.
    text: str           # the matched substring (kept here to allow audit; never written to corpus)
    start: int
    end: int
    source: str = "regex"  # "regex" | "gliner-pii"


@dataclass
class RedactedResult:
    redacted: str
    entities: list[PIIEntity] = field(default_factory=list)


def _apply_regex_rules(text: str) -> RedactedResult:
    entities: list[PIIEntity] = []
    cursor = 0
    out: list[str] = []
    matches: list[tuple[int, int, str, str]] = []
    for tag, rx in _REGEX_RULES:
        for m in rx.finditer(text):
            matches.append((m.start(), m.end(), tag, m.group(0)))
    matches.sort()
    # Drop overlaps — earlier (more specific) patterns win.
    filtered: list[tuple[int, int, str, str]] = []
    last_end = -1
    for s, e, tag, t in matches:
        if s < last_end:
            continue
        filtered.append((s, e, tag, t))
        last_end = e
    for s, e, tag, t in filtered:
        out.append(text[cursor:s])
        out.append(f"[{tag}]")
        entities.append(PIIEntity(type=tag, text=t, start=s, end=e, source="regex"))
        cursor = e
    out.append(text[cursor:])
    return RedactedResult(redacted="".join(out), entities=entities)


_GLINER_SYSTEM = """\
You are a PII redaction model. Identify all personally identifiable information in the
INPUT text. Output JSON only:

{
  "entities": [
    {"type": "PERSON" | "EMAIL" | "PHONE" | "ADDRESS" | "ORG" | "LOCATION" | "OTHER",
     "text": "<exact substring>", "start": <int>, "end": <int>}
  ]
}

Strict JSON, no prose. If no PII found, return {"entities": []}.
"""


async def _gliner_redact(client: NvidiaClient, model: str, text: str) -> Optional[RedactedResult]:
    """Attempt PII extraction via NVIDIA NIM. Return None on any failure
    (caller falls back to regex). Treats the model as chat-completions even
    though it's NER under the hood — NVIDIA NIM tends to expose models that way."""
    try:
        resp = await client.chat(
            model=model,
            messages=[
                {"role": "system", "content": _GLINER_SYSTEM},
                {"role": "user", "content": text},
            ],
            max_tokens=600,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        log.debug("gliner-pii call failed (%s); falling back to regex", e.__class__.__name__)
        return None

    parsed_text = resp.text.strip()
    try:
        parsed = json.loads(parsed_text)
    except json.JSONDecodeError:
        log.debug("gliner-pii returned non-JSON; falling back to regex")
        return None

    raw_entities = parsed.get("entities") or []
    entities: list[PIIEntity] = []
    for r in raw_entities:
        try:
            s, e = int(r["start"]), int(r["end"])
        except (KeyError, ValueError, TypeError):
            continue
        if not (0 <= s < e <= len(text)):
            continue
        entities.append(PIIEntity(
            type=str(r.get("type", "OTHER")),
            text=text[s:e],
            start=s,
            end=e,
            source="gliner-pii",
        ))
    if not entities:
        return RedactedResult(redacted=text, entities=[])

    entities.sort(key=lambda x: x.start)
    out: list[str] = []
    cursor = 0
    for ent in entities:
        if ent.start < cursor:
            continue
        out.append(text[cursor:ent.start])
        out.append(f"[{ent.type}]")
        cursor = ent.end
    out.append(text[cursor:])
    return RedactedResult(redacted="".join(out), entities=entities)


@dataclass
class PIIRedactor:
    """Public interface. Tries gliner-pii, then regex."""

    client: Optional[NvidiaClient] = None
    model: Optional[str] = None
    use_nvidia: bool = True

    def resolved_model(self) -> str:
        return self.model or model_for("pii")

    async def redact(self, text: str) -> RedactedResult:
        if not text:
            return RedactedResult(redacted=text, entities=[])
        if self.use_nvidia and self.client is not None:
            attempt = await _gliner_redact(self.client, self.resolved_model(), text)
            if attempt is not None:
                return attempt
        return _apply_regex_rules(text)

    async def redact_all(self, texts: Iterable[str]) -> list[RedactedResult]:
        return [await self.redact(t) for t in texts]


@dataclass
class SessionRedactor:
    """Wraps a PIIRedactor with per-session entity → pseudonym consistency.

    Same person across utterances → same pseudonym. Same email → same token.
    Map is reset per session, never persisted.
    """

    base: PIIRedactor
    entity_map: dict[str, str] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)
    redaction_log: list[dict] = field(default_factory=list)

    async def redact(self, text: str) -> str:
        if not text:
            return text
        result = await self.base.redact(text)
        if not result.entities:
            return text

        entities = sorted(result.entities, key=lambda e: e.start)
        out: list[str] = []
        cursor = 0
        for ent in entities:
            if ent.start < cursor:
                continue  # overlap; skip
            out.append(text[cursor:ent.start])
            out.append(self._pseudonym_for(ent.text, ent.type))
            cursor = ent.end
        out.append(text[cursor:])
        redacted = "".join(out)
        self.redaction_log.append({
            "original_len": len(text),
            "redacted_len": len(redacted),
            "entity_count": len(entities),
        })
        return redacted

    def _pseudonym_for(self, entity_text: str, entity_type: str) -> str:
        key = f"{entity_type}::{entity_text.strip().lower()}"
        existing = self.entity_map.get(key)
        if existing is not None:
            return existing
        self.counters[entity_type] = self.counters.get(entity_type, 0) + 1
        idx = self.counters[entity_type]
        pseudo = f"[{entity_type}_{idx}]"
        self.entity_map[key] = pseudo
        return pseudo

    def stats(self) -> dict:
        return {
            "entity_count": sum(self.counters.values()),
            "by_type": dict(self.counters),
            "redactions_applied": len(self.redaction_log),
        }
