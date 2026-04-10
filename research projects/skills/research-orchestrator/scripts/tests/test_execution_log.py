from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from execution_log import (
    CANONICAL_LOG_PATTERN,
    append_execution_record,
    format_log_filename,
    render_execution_record,
    resolve_task_execution_log,
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
