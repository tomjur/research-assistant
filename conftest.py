"""Pytest: put every `research projects/skills/*/scripts` on sys.path (repo root)."""

from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure(config) -> None:
    root = Path(__file__).resolve().parent
    skills = root / "research projects" / "skills"
    if not skills.is_dir():
        return
    for scripts in sorted(skills.glob("*/scripts")):
        if scripts.is_dir():
            s = str(scripts)
            if s not in sys.path:
                sys.path.insert(0, s)
