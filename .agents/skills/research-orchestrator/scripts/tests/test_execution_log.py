from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from execution_log import (
    CANONICAL_LOG_PATTERN,
    append_execution_record,
    format_log_filename,
    log_end_event,
    log_event,
    log_step,
    parse_duration_from_start,
    render_execution_record,
    resolve_task_execution_log,
    utc_timestamp_iso,
)


def test_canonical_pattern_accepts_format_log_filename() -> None:
    name = format_log_filename(datetime(2026, 4, 9, 14, 30, 52, tzinfo=timezone.utc))
    assert CANONICAL_LOG_PATTERN.match(name)


def test_canonical_pattern_rejects_legacy_short_date() -> None:
    assert CANONICAL_LOG_PATTERN.match("log_20260410.txt") is None


def test_format_log_filename_pattern() -> None:
    fixed = datetime(2026, 4, 9, 14, 30, 52, tzinfo=timezone.utc)
    assert format_log_filename(fixed) == "log_2026-04-09_143052.txt"


def test_format_log_filename_no_colons() -> None:
    name = format_log_filename()
    assert name.startswith("log_")
    assert name.endswith(".txt")
    assert ":" not in name


def test_resolve_creates_canonical_log_only(tmp_path: Path) -> None:
    log = resolve_task_execution_log(tmp_path)
    assert log.is_file()
    assert CANONICAL_LOG_PATTERN.match(log.name)
    assert not (tmp_path / "execution_log_active.txt").exists()


def test_resolve_reuses_latest_canonical_log(tmp_path: Path) -> None:
    first = resolve_task_execution_log(tmp_path)
    second = resolve_task_execution_log(tmp_path)
    assert first == second
    assert list(tmp_path.glob("log_*.txt")) == [first]


def test_resolve_picks_lexicographically_latest_when_multiple(tmp_path: Path) -> None:
    older = tmp_path / "log_2026-04-09_100000.txt"
    newer = tmp_path / "log_2026-04-10_120000.txt"
    older.write_text("", encoding="utf-8")
    newer.write_text("", encoding="utf-8")
    assert resolve_task_execution_log(tmp_path) == newer


def test_render_and_append_multiline(tmp_path: Path) -> None:
    log = tmp_path / "log_test.txt"
    rec = render_execution_record(
        "2026-04-09T14:00:00Z",
        "START",
        "worker",
        [
            ("task_id", "T1"),
            ("prompt", "line one\nline two"),
        ],
    )
    append_execution_record(log, rec)
    text = log.read_text(encoding="utf-8")
    assert "--- 2026-04-09T14:00:00Z START worker ---" in text
    assert "prompt: |" in text
    assert "  line one" in text
    assert "  line two" in text


def test_legacy_pointer_ignored_new_canonical_created(tmp_path: Path) -> None:
    (tmp_path / "execution_log_active.txt").write_text("missing.txt\n", encoding="utf-8")
    log = resolve_task_execution_log(tmp_path)
    assert log.is_file()
    assert CANONICAL_LOG_PATTERN.match(log.name)


def test_utc_timestamp_iso_z_suffix() -> None:
    s = utc_timestamp_iso(now=datetime(2026, 4, 9, 14, 30, 52, tzinfo=timezone.utc))
    assert s == "2026-04-09T14:30:52Z"
    assert s.endswith("Z")
    assert ":" in s


def test_render_roles_planning_subtask_host_subagent() -> None:
    p = render_execution_record(
        "2026-04-09T14:00:00Z",
        "START",
        "planning",
        [("planning_phase", "stage1_initial"), ("trigger", "new_task")],
    )
    assert "--- 2026-04-09T14:00:00Z START planning ---" in p
    assert "planning_phase: stage1_initial" in p

    s = render_execution_record(
        "2026-04-09T14:01:00Z",
        "START",
        "subtask",
        [("task_id", "T1"), ("subtask_dir", "sub-foo"), ("wave", "0")],
    )
    assert "START subtask" in s
    assert "subtask_dir: sub-foo" in s

    h = render_execution_record(
        "2026-04-09T14:02:00Z",
        "END",
        "host_subagent",
        [
            ("subagent_type", "explore"),
            ("purpose", "Locate TASK_GRAPH usage"),
            ("task_id", "T1"),
        ],
    )
    assert "END host_subagent" in h
    assert "subagent_type: explore" in h


def test_typical_mission_sequence_append(tmp_path: Path) -> None:
    log = tmp_path / "log_2026-04-09_140000.txt"
    blocks = [
        render_execution_record(
            "2026-04-09T14:00:00Z",
            "START",
            "planning",
            [("planning_phase", "stage1_initial")],
        ),
        render_execution_record(
            "2026-04-09T14:05:00Z",
            "END",
            "planning",
            [
                ("planning_phase", "stage1_initial"),
                ("todo_rows", "3"),
                ("task_graph_nodes", "3"),
                ("waves_computed", "yes"),
            ],
        ),
        render_execution_record(
            "2026-04-09T14:06:00Z",
            "START",
            "subtask",
            [("task_id", "T1"), ("subtask_dir", "sub-a")],
        ),
        render_execution_record(
            "2026-04-09T14:07:00Z",
            "START",
            "worker",
            [("task_id", "T1"), ("subtask_dir", "sub-a"), ("prompt_hash", "abc12345")],
        ),
    ]
    for b in blocks:
        append_execution_record(log, b)
    text = log.read_text(encoding="utf-8")
    assert text.index("START planning") < text.index("END planning")
    assert text.index("END planning") < text.index("START subtask")
    assert text.index("START subtask") < text.index("START worker")


# ---------------------------------------------------------------------------
# log_step tests
# ---------------------------------------------------------------------------


def test_log_step_appends_step_block(tmp_path: Path) -> None:
    log = tmp_path / "log_2026-04-12_140000.txt"
    fixed = datetime(2026, 4, 12, 14, 5, 0, tzinfo=timezone.utc)
    log_step(
        log,
        parent_role="planning",
        action="script_call",
        fields=[("script", "task_graph_waves.execution_waves"), ("result", "3 waves")],
        now=fixed,
    )
    text = log.read_text(encoding="utf-8")
    assert "--- 2026-04-12T14:05:00Z START step ---" in text
    assert "parent_role: planning" in text
    assert "action: script_call" in text
    assert "script: task_graph_waves.execution_waves" in text
    assert "result: 3 waves" in text


def test_log_step_no_extra_fields(tmp_path: Path) -> None:
    log = tmp_path / "log_test.txt"
    fixed = datetime(2026, 4, 12, 14, 0, 0, tzinfo=timezone.utc)
    log_step(log, parent_role="subtask", action="skill_invocation", now=fixed)
    text = log.read_text(encoding="utf-8")
    assert "parent_role: subtask" in text
    assert "action: skill_invocation" in text


def test_log_step_multiline_field(tmp_path: Path) -> None:
    log = tmp_path / "log_test.txt"
    fixed = datetime(2026, 4, 12, 14, 0, 0, tzinfo=timezone.utc)
    log_step(
        log,
        parent_role="planning",
        action="user_decision",
        fields=[("notes", "line one\nline two")],
        now=fixed,
    )
    text = log.read_text(encoding="utf-8")
    assert "notes: |" in text
    assert "  line one" in text


# ---------------------------------------------------------------------------
# parse_duration_from_start tests
# ---------------------------------------------------------------------------


def test_parse_duration_from_start_finds_matching_block(tmp_path: Path) -> None:
    log = tmp_path / "log_test.txt"
    rec = render_execution_record(
        "2026-04-12T14:00:00Z",
        "START",
        "subtask",
        [("task_id", "T1"), ("subtask_dir", "sub-a")],
    )
    append_execution_record(log, rec)
    result = parse_duration_from_start(log, "subtask", {"task_id": "T1"})
    assert result is not None
    assert result > 0  # some positive seconds since the hardcoded past timestamp


def test_parse_duration_from_start_no_match(tmp_path: Path) -> None:
    log = tmp_path / "log_test.txt"
    rec = render_execution_record(
        "2026-04-12T14:00:00Z",
        "START",
        "worker",
        [("task_id", "T1")],
    )
    append_execution_record(log, rec)
    # Looking for subtask, not worker
    result = parse_duration_from_start(log, "subtask")
    assert result is None


def test_parse_duration_from_start_missing_file(tmp_path: Path) -> None:
    result = parse_duration_from_start(tmp_path / "nonexistent.txt", "worker")
    assert result is None


# ---------------------------------------------------------------------------
# log_event / log_end_event tests
# ---------------------------------------------------------------------------


def test_log_event_generates_timestamp_at_write_time(tmp_path: Path) -> None:
    import time

    log = tmp_path / "log_test.txt"
    log_event(log, "START", "worker", [("id", "w1")])
    time.sleep(1.1)
    log_event(log, "END", "worker", [("id", "w1")])
    text = log.read_text(encoding="utf-8")
    # Extract the two timestamps
    import re

    stamps = re.findall(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)", text)
    assert len(stamps) == 2
    assert stamps[0] != stamps[1], "timestamps must differ when calls are separated by real time"


def test_log_end_event_includes_duration(tmp_path: Path) -> None:
    log = tmp_path / "log_test.txt"
    # Write a START block with a past timestamp
    rec = render_execution_record(
        "2026-01-01T00:00:00Z",
        "START",
        "subtask",
        [("task_id", "T1")],
    )
    append_execution_record(log, rec)
    log_end_event(log, "subtask", [("task_id", "T1"), ("status", "success")], {"task_id": "T1"})
    text = log.read_text(encoding="utf-8")
    assert "duration_s:" in text
    # duration should be a positive number (months since 2026-01-01)
    import re

    m = re.search(r"duration_s: (\S+)", text)
    assert m is not None
    assert float(m.group(1)) > 0


def test_log_end_event_no_matching_start(tmp_path: Path) -> None:
    log = tmp_path / "log_test.txt"
    log.write_text("", encoding="utf-8")
    log_end_event(log, "worker", [("id", "w1")])
    text = log.read_text(encoding="utf-8")
    assert "duration_s: unknown" in text


def test_parse_duration_field_mismatch(tmp_path: Path) -> None:
    log = tmp_path / "log_test.txt"
    rec = render_execution_record(
        "2026-04-12T14:00:00Z",
        "START",
        "subtask",
        [("task_id", "T1")],
    )
    append_execution_record(log, rec)
    # Wrong task_id
    result = parse_duration_from_start(log, "subtask", {"task_id": "T99"})
    assert result is None
