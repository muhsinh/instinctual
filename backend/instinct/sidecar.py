"""Per-session SQLite sidecar (v1 foundation).

Stores redacted utterances, entity extractions, tags, and embeddings as the
session progresses. One DB file per session run. The corpus writer (Phase E
of v1) consumes these sidecar files to build the long-lived training corpus.

Schema is intentionally simple — no FKs to keep writes fast and let
truncation happen by deleting the file. Embeddings are stored as raw float32
bytes (4 bytes/dim) for compactness; a small helper roundtrips them.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import aiosqlite

from .pii import PIIEntity
from .ws_protocol import UtteranceTag


_SCHEMA = """
CREATE TABLE IF NOT EXISTS utterances (
    session_id          TEXT NOT NULL,
    utterance_id        TEXT NOT NULL,
    speaker             TEXT NOT NULL,
    timestamp_seconds   REAL NOT NULL,
    raw_text            TEXT NOT NULL,
    redacted_text       TEXT NOT NULL,
    embedding           BLOB,
    embedding_dim       INTEGER,
    embedding_model     TEXT,
    PRIMARY KEY (session_id, utterance_id)
);

CREATE TABLE IF NOT EXISTS entities (
    session_id          TEXT NOT NULL,
    utterance_id        TEXT NOT NULL,
    entity_type         TEXT NOT NULL,
    entity_text         TEXT NOT NULL,
    start_offset        INTEGER NOT NULL,
    end_offset          INTEGER NOT NULL,
    source              TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entities_session_utt
    ON entities(session_id, utterance_id);

CREATE TABLE IF NOT EXISTS tags (
    session_id          TEXT NOT NULL,
    utterance_id        TEXT NOT NULL,
    intent              TEXT NOT NULL,
    confidence          REAL NOT NULL,
    topic               TEXT NOT NULL,
    references_prior    TEXT,
    raw_response        TEXT,
    model               TEXT,
    PRIMARY KEY (session_id, utterance_id)
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _pack_embedding(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack_embedding(blob: bytes, dim: int) -> list[float]:
    return list(struct.unpack(f"{dim}f", blob))


@dataclass
class Sidecar:
    path: Path

    async def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    async def write_meta(self, key: str, value: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)",
                (key, value),
            )
            await db.commit()

    async def write_utterance(
        self,
        *,
        session_id: str,
        utterance_id: str,
        speaker: str,
        timestamp_seconds: float,
        raw_text: str,
        redacted_text: str,
        entities: Iterable[PIIEntity],
        embedding: Optional[list[float]] = None,
        embedding_model: Optional[str] = None,
    ) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO utterances
                (session_id, utterance_id, speaker, timestamp_seconds,
                 raw_text, redacted_text, embedding, embedding_dim, embedding_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id, utterance_id, speaker, timestamp_seconds,
                    raw_text, redacted_text,
                    _pack_embedding(embedding) if embedding else None,
                    len(embedding) if embedding else None,
                    embedding_model,
                ),
            )
            # Replace existing entities for this utterance to keep the row
            # set canonical when redaction is re-run.
            await db.execute(
                "DELETE FROM entities WHERE session_id = ? AND utterance_id = ?",
                (session_id, utterance_id),
            )
            for ent in entities:
                await db.execute(
                    """INSERT INTO entities
                    (session_id, utterance_id, entity_type, entity_text,
                     start_offset, end_offset, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (session_id, utterance_id, ent.type, ent.text,
                     ent.start, ent.end, ent.source),
                )
            await db.commit()

    async def write_tag(
        self,
        *,
        session_id: str,
        tag: UtteranceTag,
        raw_response: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO tags
                (session_id, utterance_id, intent, confidence, topic,
                 references_prior, raw_response, model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, tag.utterance_id, tag.intent, tag.confidence,
                 tag.topic, tag.references_prior, raw_response, model),
            )
            await db.commit()

    async def utterance_count(self) -> int:
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT COUNT(*) FROM utterances") as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    async def tags_count(self) -> int:
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT COUNT(*) FROM tags") as cur:
                row = await cur.fetchone()
                return row[0] if row else 0

    async def export_summary(self) -> dict:
        async with aiosqlite.connect(self.path) as db:
            counts = {}
            for table in ("utterances", "entities", "tags"):
                async with db.execute(f"SELECT COUNT(*) FROM {table}") as cur:
                    row = await cur.fetchone()
                    counts[table] = row[0] if row else 0
            return {"path": str(self.path), "counts": counts}
