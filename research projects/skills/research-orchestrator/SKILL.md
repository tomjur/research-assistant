---
name: research-orchestrator
description: >-
  Runs one research subtask on $ControlPlaneModel$: generates unique prompt variants
  (with Python dedupe helpers), fans out workers across $ModelsForThisTask$,
  delegates validators on $ControlPlaneModel$, merges output, iterates until
  convergence or user escalation. Use one orchestrator per TODO line.
---

# Research — Orchestrator (single subtask)

**Normative spec:** Stages, isolation, and the full **orchestrator algorithm** (validation, extra prompt variants, convergence, `SHARED_CONTEXT.md`, user escalation) are in [RESEARCH_PROTOCOL.md](../../RESEARCH_PROTOCOL.md#stage-ii--subtask-execution-orchestrator-worker-validator). This file is **operational** detail for delegated runs; on conflict, follow the protocol.

## When to use

- You own **one** folder `outputs/{research-project-x}/{task-tldr}/{sub-task}/`.
- You run on **`$ControlPlaneModel$`** (this session). You coordinate **workers** and **validators** via **delegated agent runs** only (subagent, child session, or host equivalent). **Workers** use models from **`$ModelsForThisTask$`** (vary per slot). **Every validator** child must be launched with **`$ControlPlaneModel$`**, not the worker’s model. Launch **workers in parallel** across independent slots when the host supports it; **within** each **(prompt, worker model, copy)** slot, run **worker** then **validator** **sequentially**. This repo does not call LLM APIs from Python.

## Preconditions

- Read [RESEARCH_PROTOCOL.md](../../RESEARCH_PROTOCOL.md) and [docs/ROLE_BINDING.md](../../docs/ROLE_BINDING.md).
- Read task-level `USER_PROMPT.md` (including **Approved search terms (Stage I)** and **Deliverable constraints**), `TODO.md`, `TOOLS_AND_MCP.md`, and hyperparameters — especially **`$ControlPlaneModel$`** and **`$ModelsForThisTask$`**.
- **Pre-flight (before first worker delegation):** Satisfy [Stage II readiness gates](../../RESEARCH_PROTOCOL.md#stage-ii-readiness-gates) and [Delegation requirement](../../RESEARCH_PROTOCOL.md#delegation-requirement). If the **original prompt** did **not** ask to skip delegation, you **must** delegate workers and validators (this skill); do **not** collapse into inline synthesis. If **`TOOLS_AND_MCP.md`** lacks **verbatim** **`$ControlPlaneModel$`** and **`$ModelsForThisTask$`** strings, **logged user confirmation** of those IDs, or MCP/tools coverage (with documented user-approved gaps), **stop and ask**. If **Deliverable constraints** lack length/depth from the **original prompt**, from your **ask**, or from a **user-confirmed** protocol default, **stop and ask** before generating prompt variants.
- Ensure `workers/` and `validators/` subfolders exist under this `{sub-task}`.

## Prompt variants (deduplication)

Follow [RESEARCH_PROTOCOL — Orchestrator algorithm](../../RESEARCH_PROTOCOL.md#orchestrator-algorithm-per-subtask) step 1. Use **`research_utils.prompt_variants`** (`try_add_unique` / `collect_unique_prompts`, **`variant_collection_should_stop`**) per [Helper APIs](../../docs/SKILLS_AND_SCRIPTS.md#helper-apis-research_utils). On later refinement rounds, add only **new** keys; keep approved terms in every variant.

## Fan-out pattern

For each **unique prompt** × **worker model** in **`$ModelsForThisTask$`** × **copy** `1..$WorkersPerTask$`, form a **slot**; parallelize **starting** workers across slots when the host allows.

1. **Worker:** `DELEGATION_PREAMBLE_WORKER` from [ROLE_BINDING](../../docs/ROLE_BINDING.md) + [research-worker/SKILL.md](../research-worker/SKILL.md). Child runs on that slot’s **worker** model (not **`$ControlPlaneModel$`** unless also in the worker pool). Pass prompt, copy, output path `workers/worker-{model}-{copy}-{promptHash}.md` ([Filesystem structure](../../RESEARCH_PROTOCOL.md#filesystem-structure)), and `SHARED_CONTEXT.md` if present.
2. **Validator (same slot, after worker):** Launch on **`$ControlPlaneModel$`**. `DELEGATION_PREAMBLE_VALIDATOR` + [research-validator/SKILL.md](../research-validator/SKILL.md); output `validators/validator-{worker-model}-{copy}-{promptHash}.md`. Do not interleave validators ahead of unrelated workers.

Host isolation: [HOST_TOOLS](../../docs/HOST_TOOLS.md).

## Logging

- **Task-level** (`outputs/{research-project-x}/{task-tldr}/`): **`resolve_task_execution_log`** (canonical **`log_YYYY-MM-DD_HHMMSS.txt`** only; no **`execution_log_active.txt`**), then **`render_execution_record`** + **`append_execution_record`** for each child **START** / **END**. Field contract: [RESEARCH_PROTOCOL — `{task-tldr}`](../../RESEARCH_PROTOCOL.md#filesystem-structure) (Execution log bullet); API names: [Helper APIs](../../docs/SKILLS_AND_SCRIPTS.md#helper-apis-research_utils). **`PYTHONPATH`:** [HOST_TOOLS — Python](../../docs/HOST_TOOLS.md#python).
- **Sub-task:** `orchestrator_log.md` (narrative, variants, worker/validator counts), `orchestrator_responses.md` (prompt → validated pairs), optional `orchestrator_meta.json`.

## Decision rules

- If validated outputs are **empty or wholly ungrounded**, **stop** and **ask the user** how to continue (new sources, narrower question, etc.).
- If outputs **repeat** the same points, generate **new unique** prompts (subject to uniqueness + **`$MaxCountToFindUniquePrompts$`** attempt rules). When **`$MaxOrchestratorIterations$`** is set, do not exceed that many **refinement rounds** after the initial wave.
- If **no new information** appears across iterations, finish and mark the subtask complete in parent `TODO.md`.
- If validated outputs include **substantive related-work leads** that imply **new subgoals** outside this subtask, **do not** drop them: follow **Propagation** below and [RESEARCH_PROTOCOL.md — Orchestrator algorithm](../../RESEARCH_PROTOCOL.md#orchestrator-algorithm-per-subtask) step 8 (replan escalation). You **must not** add **`TODO.md`** rows or **`TASK_GRAPH.json`** nodes yourself ([docs/ROLE_BINDING.md](../../docs/ROLE_BINDING.md)).

## Propagation

- **In-subtask crucial facts:** When a worker surfaces information that **changes how remaining work in this `{sub-task}`** should proceed, append it to **`SHARED_CONTEXT.md`** (dated bullet list) and ensure **new** delegated workers read it.
- **New subgoals from related work:** When validated output implies **additional tasks** elsewhere in the mission, record the leads in **`orchestrator_log.md`** and **`SHARED_CONTEXT.md`** only if they still inform **this** subtask’s remaining runs; **ask the user** whether to run **Stage I replan** (director updates **`TODO.md`** / **`TASK_GRAPH.json`** / waves). **Do not** edit the graph or TODO for new tasks from this role.
- If propagation or escalation would **guess** user intent, **ask the user** first.

## Skills / tooling proposals

If you identify **general** reusable behavior, follow [research-skill-proposal/SKILL.md](../research-skill-proposal/SKILL.md) before editing shared skills.
