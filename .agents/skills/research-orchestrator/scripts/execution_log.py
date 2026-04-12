"""Task-level multi-agent execution log: one canonical `log_{datetime}.txt` per mission."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, TypeAlias

__all__ = [
    "append_execution_record",
    "CANONICAL_LOG_PATTERN",
    "ExecutionLogRole",
    "format_log_filename",
    "render_execution_record",
    "resolve_task_execution_log",
    "utc_timestamp_iso",
]

# Roles for the third token in `--- {iso} {phase} {role} ---`.
ExecutionLogRole: TypeAlias = Literal[
    "worker",
    "validator",
    "planning",
    "subtask",
    "host_subagent",
]

# Filenames from format_log_filename(): log_YYYY-MM-DD_HHMMSS.txt (UTC).
CANONICAL_LOG_PATTERN = re.compile(r"^log_\d{4}-\d{2}-\d{2}_\d{6}\.txt$")


def format_log_filename(now: datetime | None = None) -> str:
    """Return a filesystem-safe name like ``log_2026-04-09_143052.txt`` (UTC if ``now`` naive)."""
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    stamp = now.astimezone(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    return f"log_{stamp}.txt"


def resolve_task_execution_log(task_tldr_dir: Path | str, *, now: datetime | None = None) -> Path:
    """
    Return the path to the append-only execution log for this task folder.

    If one or more files match the canonical name pattern ``log_YYYY-MM-DD_HHMMSS.txt``,
    reuse the lexicographically greatest (latest UTC timestamp in the filename).
    Otherwise create a new file with :func:`format_log_filename` and return it.
    """
    root = Path(task_tldr_dir)
    root.mkdir(parents=True, exist_ok=True)
    canonical = sorted(
        p for p in root.glob("log_*.txt") if CANONICAL_LOG_PATTERN.match(p.name)
    )
    if canonical:
        return canonical[-1]
    name = format_log_filename(now)
    log_path = root / name
    log_path.touch(exist_ok=True)
    return log_path


def utc_timestamp_iso(*, now: datetime | None = None) -> str:
    """Return an ISO-8601 UTC timestamp ending in ``Z`` (no sub-second fraction)."""
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def render_execution_record(
    timestamp_iso: str,
    phase: Literal["START", "END"],
    role: ExecutionLogRole,
    fields: list[tuple[str, str]],
) -> str:
    """
    Format one event block for ``log_*.txt``.

    **Roles:** ``worker`` / ``validator`` (delegated research children); ``planning``
    (Stage I / director in ``{task-tldr}/``); ``subtask`` (orchestrator entering or
    leaving one ``{sub-task}/``); ``host_subagent`` (host Task or equivalent — include
    ``subagent_type`` in ``fields``).

    Multiline values use a YAML-style ``key: |`` block with two-space-indented lines.
    """
    lines: list[str] = [f"--- {timestamp_iso} {phase} {role} ---"]
    for key, value in fields:
        if "\n" in value:
            lines.append(f"{key}: |")
            for part in value.splitlines():
                lines.append(f"  {part}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("")
    return "\n".join(lines) + "\n"


def append_execution_record(log_path: Path, record: str) -> None:
    """Append a UTF-8 record to the log (creates parent dirs if needed)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(record)
