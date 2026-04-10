---
name: research-task-graph-waves
description: >-
  Builds or updates TASK_GRAPH.json (DAG of subgoals), runs Python to compute
  execution waves and topological order from completed task ids. Use at Stage I
  after decomposition and again after replanning when the graph or completion
  state changes.
---

# Research — Task graph and execution waves

**Normative context:** [RESEARCH_PROTOCOL.md](../../RESEARCH_PROTOCOL.md#planning-and-handoff) Stage I steps 5–6. Keep graphs **simple** unless parallel branches or alternatives are real: a **linear chain** is a valid graph.

## When to use

- **Initial plan:** After decomposing the user goal into orchestrator-sized subtasks, before creating `{sub-task}` folders. For academic or survey-heavy missions, decomposition should **already** reflect **survey-derived** structure (vocabulary, subareas, dependencies) per [RESEARCH_PROTOCOL.md — Survey and review literature](../../RESEARCH_PROTOCOL.md#survey-and-review-literature-when-applicable) before you author the first **`TASK_GRAPH.json`**.
- **Replan:** When new information implies **new tasks** or **new dependencies**, update `TASK_GRAPH.json` and run the helper again with an updated **`completed`** set so finished work is never rescheduled.

## Graph conventions

- **Nodes:** Each task has a stable **`id`** (slug, e.g. `01-lit-review`) and a **`description`** (human text). Align **`id`** with `TODO.md` and the planned `{sub-task}` folder naming.
- **Edges:** `[from_id, to_id]` means **`from_id` must finish before `to_id` may start**. Cycles are invalid; the Python layer raises a clear error.

## Artifact

Write **`TASK_GRAPH.json`** in the task folder (`{task-tldr}/`) next to `TODO.md`:

```json
{
  "nodes": [{ "id": "a", "description": "..." }],
  "edges": [["a", "b"]],
  "completed": []
}
```

- **`completed`:** Optional in the file; when invoking Python you **must** pass the set of **finished** node ids (from `TODO.md` checkboxes and orchestrator completion). Omit or use `[]` for “nothing done yet.”

## Python

**API:** [Helper APIs — `task_graph_waves`](../../docs/SKILLS_AND_SCRIPTS.md#helper-apis-research_utils). **`PYTHONPATH`:** [HOST_TOOLS — Python](../../docs/HOST_TOOLS.md#python).

**CLI (JSON in, JSON out):** from repository root:

```bash
PYTHONPATH="research projects/scripts" python -m research_utils.task_graph_waves < TASK_GRAPH.json
```

Or `--file path/to/TASK_GRAPH.json`.

## Agent workflow

1. Author or edit **`TASK_GRAPH.json`** (minimal DAG; parallel branches only when justified). First graph: align with [Survey and review literature](../../RESEARCH_PROTOCOL.md#survey-and-review-literature-when-applicable) when applicable (see **When to use** above).
2. Build **`completed`** from task state (ids only).
3. Run Python; read **`waves`**. **Execute the first wave** (or all tasks in the current wave in parallel when the host allows); after they finish, update **`completed`**, re-run the script for the **next** wave. Alternatively, use the full **`waves`** list as a static schedule if the graph will not change.
4. On **replan**, merge new nodes/edges into the JSON, keep **`completed`** accurate, invoke this skill again. **Do not** re-run tasks whose ids are already in **`completed`**.

## Output checklist

- [ ] `TASK_GRAPH.json` exists and matches `TODO.md` task ids
- [ ] Python run succeeded (no cycle / unknown id errors)
- [ ] Next executable wave is explicit for the session
