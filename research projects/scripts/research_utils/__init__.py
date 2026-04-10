"""Deterministic helpers for research orchestration (prompt variants, deduplication)."""

from .execution_log import (
    POINTER_NAME,
    append_execution_record,
    format_log_filename,
    render_execution_record,
    resolve_task_execution_log,
)
from .prompt_variants import (
    collect_unique_prompts,
    normalize_for_dedup,
    prompt_fingerprint,
    try_add_unique,
    variant_collection_should_stop,
)
from .task_graph_waves import (
    execution_waves,
    topological_order,
    waves_from_task_graph_json,
)

__all__ = [
    "collect_unique_prompts",
    "normalize_for_dedup",
    "prompt_fingerprint",
    "try_add_unique",
    "variant_collection_should_stop",
    "execution_waves",
    "topological_order",
    "waves_from_task_graph_json",
    "POINTER_NAME",
    "append_execution_record",
    "format_log_filename",
    "render_execution_record",
    "resolve_task_execution_log",
]
