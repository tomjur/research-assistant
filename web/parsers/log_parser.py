"""Parse log_*.txt execution logs into structured blocks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from execution_log import _HEADER_RE, CANONICAL_LOG_PATTERN

# Required fields per role, derived from RESEARCH_PROTOCOL.md + SKILL.md files.
REQUIRED_FIELDS: dict[str, dict[str, list[str]]] = {
    "planning": {
        "START": ["planning_phase"],
        "END": ["planning_phase", "todo_rows", "task_graph_nodes", "waves_computed", "duration_s"],
    },
    "subtask": {
        "START": ["id", "subtask"],
        "END": ["id", "subtask", "status", "duration_s"],
    },
    "worker": {
        "START": ["id", "subtask", "prompt_hash", "worker_model", "copy", "delegation_type"],
        "END": ["id", "subtask", "status", "artifact_paths", "prompt_hash", "worker_model", "copy", "duration_s"],
    },
    "validator": {
        "START": ["id", "subtask", "prompt_hash", "control_model", "delegation_type"],
        "END": ["id", "subtask", "status", "artifact_paths", "prompt_hash", "worker_model", "copy", "control_model", "duration_s"],
    },
    "host_subagent": {
        "START": ["subagent_type", "purpose"],
        "END": ["subagent_type", "duration_s"],
    },
    "step": {
        "START": ["parent_role", "action"],
    },
}


@dataclass
class LogBlock:
    """One parsed block from a log file."""
    timestamp: str
    phase: str  # "START" or "END"
    role: str
    fields: dict[str, str]
    warnings: list[str] = field(default_factory=list)
    raw: str = ""


@dataclass
class EventSpan:
    """A paired START/END event, or an unpaired START (still running)."""
    role: str
    start_time: str
    end_time: str | None = None
    duration_s: float | None = None
    status: str | None = None
    fields: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    children: list[EventSpan] = field(default_factory=list)
    steps: list[LogBlock] = field(default_factory=list)


def find_log_file(task_dir: Path) -> Path | None:
    """Find the latest canonical log file in a task directory."""
    candidates = sorted(
        (p for p in task_dir.glob("log_*.txt") if CANONICAL_LOG_PATTERN.match(p.name)),
    )
    return candidates[-1] if candidates else None


def parse_log_file(path: Path) -> list[LogBlock]:
    """Parse a log_*.txt file into structured blocks."""
    text = path.read_text(encoding="utf-8")
    blocks: list[LogBlock] = []

    # Split on `--- ` at start of line. The first chunk may be empty.
    raw_parts = re.split(r"(?m)^--- ", text)

    for raw in raw_parts:
        raw = raw.strip()
        if not raw:
            continue
        lines = raw.splitlines()
        # Reconstruct the header line for regex matching
        header_line = "--- " + lines[0]
        m = _HEADER_RE.match(header_line)
        if not m:
            continue

        ts, phase, role = m.group(1), m.group(2), m.group(3)
        fields: dict[str, str] = {}
        i = 1
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            if ": " in line and not line.startswith("  "):
                key, value = line.split(": ", 1)
                if value == "|":
                    # Multiline value: collect indented continuation lines
                    ml_parts: list[str] = []
                    i += 1
                    while i < len(lines) and lines[i].startswith("  "):
                        ml_parts.append(lines[i][2:])
                        i += 1
                    fields[key] = "\n".join(ml_parts)
                    continue
                else:
                    fields[key] = value
            i += 1

        block = LogBlock(
            timestamp=ts, phase=phase, role=role,
            fields=fields, raw="--- " + raw,
        )
        # Validate required fields
        role_reqs = REQUIRED_FIELDS.get(role, {})
        phase_reqs = role_reqs.get(phase, [])
        for req in phase_reqs:
            if req not in fields:
                block.warnings.append(f"Missing required field: {req}")
        blocks.append(block)

    return blocks


def pair_events(blocks: list[LogBlock]) -> list[EventSpan]:
    """Match START/END pairs into EventSpan objects.

    Pairing uses role + identifying fields (id, subtask, copy, prompt_hash).
    Step events (no END) become standalone entries.
    Unpaired STARTs indicate in-progress work.
    """
    spans: list[EventSpan] = []
    open_starts: list[tuple[LogBlock, EventSpan]] = []

    for block in blocks:
        if block.role == "step":
            span = EventSpan(
                role="step",
                start_time=block.timestamp,
                fields=block.fields,
                warnings=block.warnings,
            )
            spans.append(span)
            continue

        if block.phase == "START":
            span = EventSpan(
                role=block.role,
                start_time=block.timestamp,
                fields=dict(block.fields),
                warnings=list(block.warnings),
            )
            open_starts.append((block, span))
            spans.append(span)
        elif block.phase == "END":
            # Find matching START (scan backwards)
            match_idx = None
            for i in range(len(open_starts) - 1, -1, -1):
                start_block, start_span = open_starts[i]
                if start_block.role != block.role:
                    continue
                if _blocks_match(start_block, block):
                    match_idx = i
                    break
            if match_idx is not None:
                _, start_span = open_starts.pop(match_idx)
                start_span.end_time = block.timestamp
                start_span.status = block.fields.get("status")
                start_span.warnings.extend(block.warnings)
                # Merge END fields into span
                for k, v in block.fields.items():
                    if k not in start_span.fields:
                        start_span.fields[k] = v
                dur = block.fields.get("duration_s")
                if dur and dur != "unknown":
                    try:
                        start_span.duration_s = float(dur)
                    except ValueError:
                        pass
            else:
                # Orphan END with no matching START
                span = EventSpan(
                    role=block.role,
                    start_time=block.timestamp,
                    end_time=block.timestamp,
                    status=block.fields.get("status"),
                    fields=block.fields,
                    warnings=block.warnings + ["No matching START block found"],
                )
                dur = block.fields.get("duration_s")
                if dur and dur != "unknown":
                    try:
                        span.duration_s = float(dur)
                    except ValueError:
                        pass
                spans.append(span)

    return spans


def _blocks_match(start: LogBlock, end: LogBlock) -> bool:
    """Check if a START and END block refer to the same event."""
    match_keys = ["id", "subtask", "copy", "prompt_hash", "planning_phase", "subagent_type"]
    for key in match_keys:
        sv = start.fields.get(key)
        ev = end.fields.get(key)
        if sv is not None and ev is not None and sv != ev:
            return False
    return True
