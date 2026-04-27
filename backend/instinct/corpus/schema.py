"""Corpus schema (v1, #7).

Single SQLite file per team. Versioned, timestamped, foreign-keyed.
Designed to be diffed and migrated as fields are added; downstream RL /
fine-tuning consumers join across these tables to assemble (meeting →
artifact → outcome) chains.

When migrating to Postgres + pgvector later, the table shapes hold; only
the embedding storage column types change.
"""

CORPUS_SCHEMA_VERSION = "v1.0.0"


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS corpus_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS corpus_sessions (
    session_id        TEXT PRIMARY KEY,
    team_id           TEXT NOT NULL,
    started_at_ts     REAL NOT NULL,
    ended_at_ts       REAL NOT NULL,
    duration_s        REAL NOT NULL,
    schema_version    TEXT NOT NULL,
    user_context_hash TEXT,
    cost_estimated_usd REAL,
    cost_paused       INTEGER NOT NULL DEFAULT 0,
    written_at_ts     REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS corpus_utterances (
    session_id        TEXT NOT NULL,
    utterance_id      TEXT NOT NULL,
    speaker           TEXT NOT NULL,
    timestamp_seconds REAL NOT NULL,
    redacted_text     TEXT NOT NULL,
    intent            TEXT,
    intent_confidence REAL,
    topic             TEXT,
    thread_id         TEXT,
    PRIMARY KEY (session_id, utterance_id),
    FOREIGN KEY (session_id) REFERENCES corpus_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS corpus_threads (
    session_id              TEXT NOT NULL,
    thread_id               TEXT NOT NULL,
    inferred_topic          TEXT NOT NULL,
    archetype               TEXT,
    archetype_confidence    REAL,
    started_at_ts           REAL NOT NULL,
    started_at_utterance_id TEXT,
    final_spec_markdown     TEXT,
    PRIMARY KEY (session_id, thread_id),
    FOREIGN KEY (session_id) REFERENCES corpus_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS corpus_build_plans (
    session_id     TEXT NOT NULL,
    thread_id      TEXT NOT NULL,
    version        INTEGER NOT NULL,
    archetype      TEXT NOT NULL,
    plan_json      TEXT NOT NULL,
    written_at_ts  REAL NOT NULL,
    PRIMARY KEY (session_id, thread_id, version),
    FOREIGN KEY (session_id, thread_id)
        REFERENCES corpus_threads(session_id, thread_id)
);

CREATE TABLE IF NOT EXISTS corpus_build_results (
    session_id        TEXT NOT NULL,
    thread_id         TEXT NOT NULL,
    output_dir        TEXT NOT NULL,
    files_generated_json TEXT NOT NULL,
    validation_passed INTEGER NOT NULL,
    validation_detail_json TEXT,
    cost_usd          REAL NOT NULL DEFAULT 0,
    mode              TEXT NOT NULL,
    error             TEXT,
    written_at_ts     REAL NOT NULL,
    PRIMARY KEY (session_id, thread_id),
    FOREIGN KEY (session_id, thread_id)
        REFERENCES corpus_threads(session_id, thread_id)
);

CREATE TABLE IF NOT EXISTS corpus_artifact_files (
    session_id     TEXT NOT NULL,
    thread_id      TEXT NOT NULL,
    relative_path  TEXT NOT NULL,
    content        TEXT NOT NULL,
    sha256         TEXT NOT NULL,
    size_bytes     INTEGER NOT NULL,
    written_at_ts  REAL NOT NULL,
    PRIMARY KEY (session_id, thread_id, relative_path),
    FOREIGN KEY (session_id, thread_id)
        REFERENCES corpus_threads(session_id, thread_id)
);

CREATE TABLE IF NOT EXISTS corpus_clarifications (
    session_id        TEXT NOT NULL,
    thread_id         TEXT NOT NULL,
    clarification_id  TEXT NOT NULL,
    question          TEXT NOT NULL,
    options_json      TEXT NOT NULL,
    outcome           TEXT NOT NULL,
    timed_out         INTEGER NOT NULL,
    PRIMARY KEY (session_id, clarification_id),
    FOREIGN KEY (session_id, thread_id)
        REFERENCES corpus_threads(session_id, thread_id)
);

CREATE TABLE IF NOT EXISTS corpus_feasibility (
    session_id          TEXT NOT NULL,
    thread_id           TEXT NOT NULL,
    service             TEXT NOT NULL,
    reachable           INTEGER NOT NULL,
    issue               TEXT,
    suggested_alternatives_json TEXT,
    written_at_ts       REAL NOT NULL,
    FOREIGN KEY (session_id, thread_id)
        REFERENCES corpus_threads(session_id, thread_id)
);

CREATE TABLE IF NOT EXISTS corpus_deployments (
    session_id    TEXT NOT NULL,
    thread_id     TEXT NOT NULL,
    deployer      TEXT NOT NULL,
    success       INTEGER NOT NULL,
    url           TEXT,
    detail_json   TEXT,
    error         TEXT,
    written_at_ts REAL NOT NULL,
    PRIMARY KEY (session_id, thread_id, deployer),
    FOREIGN KEY (session_id, thread_id)
        REFERENCES corpus_threads(session_id, thread_id)
);

CREATE TABLE IF NOT EXISTS corpus_feedback (
    session_id     TEXT NOT NULL,
    thread_id      TEXT NOT NULL,
    user_signal    TEXT NOT NULL,            -- accepted | rejected | edited | ignored
    rationale      TEXT,
    written_at_ts  REAL NOT NULL,
    PRIMARY KEY (session_id, thread_id),
    FOREIGN KEY (session_id, thread_id)
        REFERENCES corpus_threads(session_id, thread_id)
);
"""
