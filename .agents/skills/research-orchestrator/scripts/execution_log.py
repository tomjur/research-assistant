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
    "log_end_event",
    "log_event",
    "log_step",
    "parse_duration_from_start",
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
    "step",
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


# ---------------------------------------------------------------------------
# High-level logging (timestamp generated at write-time)
# ---------------------------------------------------------------------------


def log_event(
    log_path: Path,
    phase: Literal["START", "END"],
    role: ExecutionLogRole,
    fields: list[tuple[str, str]],
) -> None:
    """
    Append a START or END block with the timestamp captured **at call time**.

    Preferred over calling ``utc_timestamp_iso`` → ``render_execution_record``
    → ``append_execution_record`` manually, because the timestamp cannot be
    reused or batched by the caller.
    """
    ts = utc_timestamp_iso()
    record = render_execution_record(ts, phase, role, fields)
    append_execution_record(log_path, record)


def log_end_event(
    log_path: Path,
    role: ExecutionLogRole,
    fields: list[tuple[str, str]],
    match_fields: dict[str, str] | None = None,
) -> None:
    """
    Append an END block with **auto-computed** ``duration_s``.

    Calls :func:`parse_duration_from_start` to find the matching START block
    and compute wall-clock seconds, then appends ``duration_s`` to *fields*
    before writing.  If no matching START is found, ``duration_s`` is recorded
    as ``"unknown"``.
    """
    duration = parse_duration_from_start(log_path, role, match_fields)
    duration_val = str(duration) if duration is not None else "unknown"
    all_fields = list(fields) + [("duration_s", duration_val)]
    log_event(log_path, "END", role, all_fields)


# ---------------------------------------------------------------------------
# Lightweight step logging (single block, no START/END pair needed)
# ---------------------------------------------------------------------------

def log_step(
    log_path: Path,
    parent_role: ExecutionLogRole,
    action: str,
    fields: list[tuple[str, str]] | None = None,
    *,
    now: datetime | None = None,
) -> None:
    """
    Append a single ``STEP`` block that records a discrete action within a phase.

    Unlike worker/validator/planning blocks, steps do **not** require paired
    START/END — they capture point-in-time events such as script calls, skill
    invocations, user decisions, or dedup stats.

    ``parent_role`` is the role of the enclosing phase (e.g. ``"planning"``,
    ``"subtask"``). The block is rendered with role ``step`` and includes
    ``parent_role`` and ``action`` as fields automatically.
    """
    ts = utc_timestamp_iso(now=now)
    all_fields: list[tuple[str, str]] = [
        ("parent_role", parent_role),
        ("action", action),
    ]
    if fields:
        all_fields.extend(fields)
    record = render_execution_record(ts, "START", "step", all_fields)
    append_execution_record(log_path, record)


# ---------------------------------------------------------------------------
# Duration helpers
# ---------------------------------------------------------------------------

_HEADER_RE = re.compile(
    r"^--- (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) (START|END) (\S+) ---$"
)


def parse_duration_from_start(
    log_path: Path,
    role: ExecutionLogRole,
    match_fields: dict[str, str] | None = None,
) -> float | None:
    """
    Scan *backwards* for the most recent ``START`` block of *role* whose fields
    are a superset of *match_fields*, and return wall-clock seconds from that
    timestamp to now (UTC).

    Returns ``None`` if no matching START is found.  Useful for computing
    ``duration_s`` when appending an END block.
    """
    if not log_path.exists():
        return None
    text = log_path.read_text(encoding="utf-8")
    blocks = text.split("--- ")
    # Walk backwards (most recent first).
    for raw in reversed(blocks):
        if not raw.strip():
            continue
        lines = raw.splitlines()
        header_line = "--- " + lines[0]
        m = _HEADER_RE.match(header_line)
        if not m:
            continue
        ts_str, phase, blk_role = m.group(1), m.group(2), m.group(3)
        if phase != "START" or blk_role != role:
            continue
        if match_fields:
            blk_fields = {}
            for line in lines[1:]:
                if ": " in line and not line.startswith("  "):
                    k, v = line.split(": ", 1)
                    if not v.startswith("|"):
                        blk_fields[k] = v
            if not all(blk_fields.get(k) == v for k, v in match_fields.items()):
                continue
        # Parse the START timestamp and compute delta.
        start_dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        delta = datetime.now(timezone.utc) - start_dt
        return round(delta.total_seconds(), 1)
    return None
