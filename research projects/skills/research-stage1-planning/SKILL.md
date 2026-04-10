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

- Starting a **new** task under `research projects/{research-project-x}/{task-tldr}/`.
- Before any orchestrator folders exist or workers run.

## Instructions

1. **Read** [RESEARCH_PROTOCOL.md](../../RESEARCH_PROTOCOL.md) hyperparameters; copy chosen values into the task folder (e.g. `HYPERPARAMETERS.md` or the front matter of `TOOLS_AND_MCP.md`).
2. **Capture** the raw user request in `USER_PROMPT.md` (see [templates/USER_PROMPT.md](../../templates/USER_PROMPT.md)).
3. **Search terms:** [RESEARCH_PROTOCOL — Search terms (first)](../../RESEARCH_PROTOCOL.md#search-terms-first): web-validate each candidate (**do not** guess); persist approvals in `USER_PROMPT.md` **Approved search terms** with basis; ambiguous terms → user + **Clarifications**.
4. **Survey / review (when applicable):** [RESEARCH_PROTOCOL — Survey and review literature](../../RESEARCH_PROTOCOL.md#survey-and-review-literature-when-applicable). Fold vocabulary and structure into decomposition **before** locking **`TASK_GRAPH.json`**. Skip or minimize when clearly non-academic.
5. **Decompose** into subtasks (orchestrator-sized). Each subtask should be one coherent question or work package. Write `TODO.md` with:
   - Stable **task id** per row (same string as the graph node `id`; see [templates/TODO.md](../../templates/TODO.md))
   - Checkbox per subtask
   - Planned `{sub-task}` folder name (slug, no spaces recommended)
   - Dependencies (if any), consistent with `TASK_GRAPH.json` edges
   Then follow **[research-task-graph-waves/SKILL.md](../research-task-graph-waves/SKILL.md)**: author **`TASK_GRAPH.json`** (nodes + edges; optional `completed`), run **`research_utils.task_graph_waves`** (`execution_waves` / `waves_from_task_graph_json`) so **waves** and **topological order** are computed deterministically. On later replans, update the JSON and re-run with an accurate **`completed`** set.
6. **Interview the user** until scope, deliverable shape, source constraints, and success criteria are unambiguous (max a few focused questions per round). **Report length / depth:** if the original request does not specify how long or deep **`FINAL_RESPONSE.md`** (and overall output) should be, **ask** the user and record the answer under **`USER_PROMPT.md`** — **Deliverable constraints** (words, pages, or qualitative level). Alternatively record an explicit waiver (e.g. protocol default depth) there so Stage II can proceed.
7. **Tools, MCP, models:** Repo index [AGENTS.md](../../../AGENTS.md); defaults [SKILLS_AND_SCRIPTS](../../docs/SKILLS_AND_SCRIPTS.md); hosts [HOST_TOOLS](../../docs/HOST_TOOLS.md). **Model IDs:** [RESEARCH_PROTOCOL — LLM / model IDs](../../RESEARCH_PROTOCOL.md#llm--model-ids). Before `TOOLS_AND_MCP.md`, satisfy [Planning and handoff](../../RESEARCH_PROTOCOL.md#planning-and-handoff) step 9 and [Stage II readiness gates](../../RESEARCH_PROTOCOL.md#stage-ii-readiness-gates).
8. Write **`TOOLS_AND_MCP.md`** from [templates/](../../templates/TOOLS_AND_MCP.md) with **`$ControlPlaneModel$`** and **`$ModelsForThisTask$`**.
9. **Isolation:** Do **not** read other `{research-project-x}` trees; you **may** skim prior **`FINAL_RESPONSE.md`** under the same project.

## Output checklist

- [ ] `USER_PROMPT.md` (original request, **Deliverable constraints** filled or explicit waiver, **Approved search terms** with web basis, clarifications)
- [ ] `TODO.md` (task ids aligned with `TASK_GRAPH.json`)
- [ ] `TASK_GRAPH.json` and Python-computed **waves** (or note in `TODO.md` / log where waves are recorded)
- [ ] `TOOLS_AND_MCP.md` (+ optional `MODELS.md`)
- [ ] Hyperparameters recorded
