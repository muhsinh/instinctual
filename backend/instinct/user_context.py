"""User-authored context loader (Amendment 4).

The file at ~/.instinct/context.md is user-owned. Backend reads it once at
session start and snapshots the contents into SessionState.user_context. No
code path writes to it; that read-only contract is enforced by absence.
"""

from __future__ import annotations

from pathlib import Path

CONTEXT_PATH = Path.home() / ".instinct" / "context.md"
HARD_LIMIT_BYTES = 8 * 1024
SOFT_WARN_BYTES = 4 * 1024

SEED_TEMPLATE = """# Instinct context

Standing context loaded into every agent's prompt at session start.
Read-only for agents — they will never modify this file.

## Suggested sections
- Project background: what you're working on
- Team / who: people and their roles
- Jargon: domain vocabulary your meetings use
- Ongoing initiatives: things in flight
- Naming conventions: how you name things

Keep this tight (under ~4KB / ~1000 words). Hard cap is 8KB; sessions refuse
to start above that.
"""


class ContextTooLargeError(RuntimeError):
    """Raised when ~/.instinct/context.md exceeds HARD_LIMIT_BYTES."""


def ensure_context_file(path: Path = CONTEXT_PATH) -> Path:
    """Create the context file with a seed template if missing. Idempotent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(SEED_TEMPLATE, encoding="utf-8")
    return path


def load_user_context(path: Path = CONTEXT_PATH) -> str:
    """Snapshot ~/.instinct/context.md for one session. Raises on size violation."""
    p = ensure_context_file(path)
    raw = p.read_text(encoding="utf-8")
    size = len(raw.encode("utf-8"))
    if size > HARD_LIMIT_BYTES:
        raise ContextTooLargeError(
            f"{p} is {size} bytes (limit {HARD_LIMIT_BYTES}). Trim before starting a session."
        )
    return raw


def context_size_warning(text: str) -> str | None:
    """Return a soft warning string when the file is in the warn band, else None."""
    size = len(text.encode("utf-8"))
    if size > SOFT_WARN_BYTES:
        return f"User context is {size} bytes (>{SOFT_WARN_BYTES} soft warn; hard limit {HARD_LIMIT_BYTES})."
    return None
