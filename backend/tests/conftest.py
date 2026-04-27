from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Location of the hand-built Phase-1 fixtures."""
    return Path(__file__).resolve().parent.parent / "eval" / "fixtures"
