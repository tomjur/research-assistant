"""Task-level multi-agent execution log: one `log_{datetime}.txt` per user prompt (mission)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

# Orchestrator resolves the active log via this pointer in `{task-tldr}/`.
__all__ = [
    "POINTER_NAME",
    "append_execution_record",
    "format_log_filename",
    "render_execution_record",
    "resolve_task_execution_log",
]

POINTER_NAME = "execution_log_active.txt"


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

    If ``execution_log_active.txt`` exists and names an existing file in the same
    directory, reuse it. Otherwise create a new ``log_YYYY-MM-DD_HHMMSS.txt`` and
    write the pointer.
    """
    root = Path(task_tldr_dir)
    root.mkdir(parents=True, exist_ok=True)
    pointer = root / POINTER_NAME
    if pointer.is_file():
        basename = pointer.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if basename:
            candidate = root / basename
            if candidate.is_file():
                return candidate
    name = format_log_filename(now)
    log_path = root / name
    log_path.touch(exist_ok=True)
    pointer.write_text(name + "\n", encoding="utf-8")
    return log_path


def render_execution_record(
    timestamp_iso: str,
    phase: Literal["START", "END"],
    role: Literal["worker", "validator"],
    fields: list[tuple[str, str]],
) -> str:
    """
    Format one event block for ``log_*.txt``.

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
