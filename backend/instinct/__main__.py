"""Run the Instinct backend: `python -m instinct`."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    log_level = os.getenv("INSTINCT_LOG_LEVEL", "info")
    uvicorn.run(
        "instinct.server:app",
        host="127.0.0.1",
        port=8765,
        log_level=log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
