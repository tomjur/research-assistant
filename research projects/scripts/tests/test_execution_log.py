from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


from research_utils.execution_log import (
    POINTER_NAME,
    append_execution_record,
    format_log_filename,
    render_execution_record,
    resolve_task_execution_log,
)


def test_format_log_filename_pattern() -> None:
    fixed = datetime(2026, 4, 9, 14, 30, 52, tzinfo=timezone.utc)
    assert format_log_filename(fixed) == "log_2026-04-09_143052.txt"


def test_format_log_filename_no_colons() -> None:
    name = format_log_filename()
    assert name.startswith("log_")
    assert name.endswith(".txt")
    assert ":" not in name


def test_resolve_creates_log_and_pointer(tmp_path: Path) -> None:
    log = resolve_task_execution_log(tmp_path)
    assert log.is_file()
    assert log.name.startswith("log_") and log.name.endswith(".txt")
    pointer = tmp_path / POINTER_NAME
    assert pointer.read_text(encoding="utf-8").strip() == log.name


def test_resolve_reuses_existing_via_pointer(tmp_path: Path) -> None:
    first = resolve_task_execution_log(tmp_path)
    second = resolve_task_execution_log(tmp_path)
    assert first == second
    assert list(tmp_path.glob("log_*.txt")) == [first]


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


def test_broken_pointer_recreates_log(tmp_path: Path) -> None:
    (tmp_path / POINTER_NAME).write_text("missing.txt\n", encoding="utf-8")
    log = resolve_task_execution_log(tmp_path)
    assert log.is_file()
    assert log.name != "missing.txt"
