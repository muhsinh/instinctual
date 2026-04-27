# Instinct

Meeting → spec document, live, on macOS. v0.

A menu bar app captures internal meeting audio, streams it to a Python backend that runs five concurrent Claude agents over a shared session state, and produces a structured spec by end-of-meeting.

## Repo layout

- `backend/` — Python (FastAPI + asyncio) WebSocket server, transcription, agent orchestration, eval harness
- `mac/` — Swift/SwiftUI menu bar app (Phase 3)

## Quick start (backend, Phase 1)

```sh
cd backend
cp .env.example .env       # fill in ANTHROPIC_API_KEY, DEEPGRAM_API_KEY
uv sync
uv run pytest
uv run python -m instinct.eval.replay eval/fixtures/clean --speed max
```

See `/Users/muh/.claude/plans/here-s-a-claude-code-agile-origami.md` for the full implementation plan.
