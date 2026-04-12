"""Discover research projects and tasks from the outputs/ directory."""

from __future__ import annotations

import json
from pathlib import Path


def list_projects(outputs_dir: Path) -> list[dict]:
    """Return [{name, path, tasks}] for each project directory under outputs/."""
    if not outputs_dir.is_dir():
        return []
    projects = []
    for p in sorted(outputs_dir.iterdir()):
        if p.is_dir() and not p.name.startswith("."):
            tasks = list_tasks(p)
            projects.append({"name": p.name, "path": p, "tasks": tasks})
    return projects


def list_tasks(project_dir: Path) -> list[dict]:
    """Return [{tldr, path, status}] for each task under a project.

    Status: 'completed' | 'in_progress' | 'planning'.
    Active (non-completed) tasks sort first.
    """
    if not project_dir.is_dir():
        return []
    tasks = []
    for t in sorted(project_dir.iterdir()):
        if t.is_dir() and not t.name.startswith("."):
            status = _detect_status(t)
            tasks.append({"tldr": t.name, "path": t, "status": status})
    # Active tasks first, then completed
    order = {"planning": 0, "in_progress": 1, "completed": 2}
    tasks.sort(key=lambda x: (order.get(x["status"], 9), x["tldr"]))
    return tasks


def task_dir_for(outputs_dir: Path, project: str, task: str) -> Path | None:
    """Resolve a task directory from project + task slug. Returns None if missing."""
    td = outputs_dir / project / task
    if td.is_dir():
        return td
    return None


def _detect_status(task_dir: Path) -> str:
    """Determine task status from filesystem markers."""
    if (task_dir / "FINAL_RESPONSE.md").exists():
        return "completed"
    tg = task_dir / "TASK_GRAPH.json"
    if tg.exists():
        try:
            data = json.loads(tg.read_text(encoding="utf-8"))
            nodes = data.get("nodes", [])
            completed = set(data.get("completed", []))
            node_ids = {(n["id"] if isinstance(n, dict) else n) for n in nodes}
            if node_ids and not node_ids.issubset(completed):
                return "in_progress"
            # All nodes completed but no FINAL_RESPONSE.md yet
            if node_ids and node_ids.issubset(completed):
                return "in_progress"
        except (json.JSONDecodeError, KeyError):
            return "in_progress"
    return "planning"
