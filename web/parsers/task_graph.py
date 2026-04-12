"""Load TASK_GRAPH.json and compute execution waves."""

from __future__ import annotations

import json
from pathlib import Path

from task_graph_waves import waves_from_task_graph_json


def load_task_graph_with_waves(task_dir: Path) -> dict:
    """Load TASK_GRAPH.json and compute waves.

    Returns {
        nodes: [{id, description}],
        edges: [[from, to]],
        completed: set[str],
        waves: [[ids]],
        topological_order: [ids],
        remaining_count: int,
    }
    """
    tg_path = task_dir / "TASK_GRAPH.json"
    if not tg_path.exists():
        raise FileNotFoundError("TASK_GRAPH.json not found")
    data = json.loads(tg_path.read_text(encoding="utf-8"))
    result = waves_from_task_graph_json(data)
    return {
        "nodes": data.get("nodes", []),
        "edges": data.get("edges", []),
        "completed": set(data.get("completed", [])),
        "waves": result["waves"],
        "topological_order": result["topological_order"],
        "remaining_count": result["remaining_count"],
    }
