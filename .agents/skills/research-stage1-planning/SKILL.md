---
name: research-stage1-planning
description: >-
  Extracts search-relevant terms (web-vetted), runs a survey/review literature pass
  when applicable, saves approved terms with the prompt, decomposes the query into
  subtasks, authors TASK_GRAPH.json and execution waves via Python, maintains
  TODO.md, resolves ambiguity with the user, and records tools/skills/MCP. Use at
  Stage I before spawning orchestrators.
---

# Research — Stage I planning

## When to use

- Starting a **new** task under `outputs/{research-project-x}/{task-tldr}/` (path from the repository root).
- Before any orchestrator folders exist or workers run.

## Instructions

1. **Read** [RESEARCH_PROTOCOL.md](../../research%20projects/RESEARCH_PROTOCOL.md) hyperparameters; copy chosen values into the task folder (e.g. `HYPERPARAMETERS.md` or the front matter of `TOOLS_AND_MCP.md`).
2. **Task-level execution log (planning):** In **`outputs/{research-project-x}/{task-tldr}/`**, call **`resolve_task_execution_log`**, then **`append_execution_record`** with **`render_execution_record`** using **`utc_timestamp_iso()`**, **`planning`**, **START**, fields at least **`planning_phase`:** `stage1_initial` (optional **`trigger`:** e.g. `new_task` / `user_replan`). On **Stage I replan** of an existing mission, log another **START**/**END** pair with **`planning_phase`:** `stage1_replan` before and after that replan pass. **END** **planning** only when the [Output checklist](#output-checklist) artifacts for that pass are satisfied, with **END** fields including **`todo_rows`**, **`task_graph_nodes`**, **`waves_computed`:** `yes` or `no`. API names: [Helper APIs](../../research%20projects/docs/SKILLS_AND_SCRIPTS.md#helper-apis). **`PYTHONPATH`:** [HOST_TOOLS — Python](../../research%20projects/docs/HOST_TOOLS.md#python).
3. **Capture** the raw user request in `USER_PROMPT.md` (see [templates/USER_PROMPT.md](../../research%20projects/templates/USER_PROMPT.md)).
4. **Search terms:** [RESEARCH_PROTOCOL — Search terms (first)](../../research%20projects/RESEARCH_PROTOCOL.md#search-terms-first): web-validate each candidate (**do not** guess); persist approvals in `USER_PROMPT.md` **Approved search terms** with basis; ambiguous terms → user + **Clarifications**.
5. **Survey / review (when applicable):** [RESEARCH_PROTOCOL — Survey and review literature](../../research%20projects/RESEARCH_PROTOCOL.md#survey-and-review-literature-when-applicable). Fold vocabulary and structure into decomposition **before** locking **`TASK_GRAPH.json`**. Skip or minimize when clearly non-academic.
6. **Decompose** into subtasks (orchestrator-sized). Each subtask should be one coherent question or work package. Write `TODO.md` with:
   - Stable **task id** per row (same string as the graph node `id`; see [templates/TODO.md](../../research%20projects/templates/TODO.md))
   - Checkbox per subtask
   - Planned `{sub-task}` folder name (slug, no spaces recommended)
   - Dependencies (if any), consistent with `TASK_GRAPH.json` edges
   Then follow **[research-task-graph-waves/SKILL.md](../research-task-graph-waves/SKILL.md)**: author **`TASK_GRAPH.json`** (nodes + edges; optional `completed`), run **`task_graph_waves`** (`execution_waves` / `waves_from_task_graph_json`) so **waves** and **topological order** are computed deterministically. On later replans, update the JSON and re-run with an accurate **`completed`** set.
7. **Interview the user** until scope, deliverable shape, source constraints, and success criteria are unambiguous (max a few focused questions per round). **Deliverable constraints:** follow [RESEARCH_PROTOCOL — step 8](../../research%20projects/RESEARCH_PROTOCOL.md#planning-and-handoff) and record in **`USER_PROMPT.md`**.
8. **Delegation:** [RESEARCH_PROTOCOL — Delegation requirement](../../research%20projects/RESEARCH_PROTOCOL.md#delegation-requirement). Do **not** plan a single-session skip of workers/validators unless the **original prompt** explicitly requests it.
9. **Tools, MCP, models:** Repo index [AGENTS.md](../../../AGENTS.md); defaults [SKILLS_AND_SCRIPTS](../../research%20projects/docs/SKILLS_AND_SCRIPTS.md); hosts [HOST_TOOLS](../../research%20projects/docs/HOST_TOOLS.md). **Model IDs:** [RESEARCH_PROTOCOL — LLM / model IDs](../../research%20projects/RESEARCH_PROTOCOL.md#llm--model-ids) — **verbatim** strings and **logged user confirmation**. Before `TOOLS_AND_MCP.md`, satisfy [Planning and handoff](../../research%20projects/RESEARCH_PROTOCOL.md#planning-and-handoff) step 9, [Default robustness](../../research%20projects/RESEARCH_PROTOCOL.md#hyperparameters), and [Stage II readiness gates](../../research%20projects/RESEARCH_PROTOCOL.md#stage-ii-readiness-gates).
10. Write **`TOOLS_AND_MCP.md`** from [templates/](../../research%20projects/templates/TOOLS_AND_MCP.md) with **`$ControlPlaneModel$`** and **`$ModelsForThisTask$`**.
11. **Isolation:** Do **not** read other `outputs/{research-project-x}` trees; you **may** skim prior **`FINAL_RESPONSE.md`** under the same **`outputs/{research-project-x}/`** program.

## Output checklist

- [ ] Task-level **`log_*.txt`:** **`planning`** **START** (step 2) and **`planning`** **END** with **`todo_rows`**, **`task_graph_nodes`**, **`waves_computed`** for this pass
- [ ] `USER_PROMPT.md` (original request, **Deliverable constraints** from original prompt / user answer / **user-confirmed** default only, **Model confirmation** if applicable, **Approved search terms** with web basis, clarifications)
- [ ] `TODO.md` (task ids aligned with `TASK_GRAPH.json`)
- [ ] `TASK_GRAPH.json` and Python-computed **waves** (or note in `TODO.md` / log where waves are recorded)
- [ ] `TOOLS_AND_MCP.md` (+ optional `MODELS.md`)
- [ ] Hyperparameters recorded
