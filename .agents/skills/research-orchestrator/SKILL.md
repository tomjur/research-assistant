---
name: research-orchestrator
description: >-
  Runs one research subtask on $ControlPlaneModel$: generates unique prompt variants
  (with Python dedupe helpers), fans out workers across $ModelsForThisTask$,
  delegates validators on $ControlPlaneModel$, merges output, iterates until
  convergence or user escalation. Use one orchestrator per TODO line.
---

# Research — Orchestrator (single subtask)

**Normative spec:** Stages, isolation, and the full **orchestrator algorithm** (validation, extra prompt variants, convergence, `SHARED_CONTEXT.md`, user escalation) are in [RESEARCH_PROTOCOL.md](../../research%20projects/RESEARCH_PROTOCOL.md#stage-ii--subtask-execution-orchestrator-worker-validator). This file is **operational** detail for delegated runs; on conflict, follow the protocol.

## When to use

- You own **one** folder `outputs/{research-project-x}/{task-tldr}/{sub-task}/`.
- You run on **`$ControlPlaneModel$`** (this session). You coordinate **workers** and **validators** via **delegated agent runs** only (subagent, child session, or host equivalent). **Workers** use models from **`$ModelsForThisTask$`** (vary per slot). **Every validator** child must be launched with **`$ControlPlaneModel$`**, not the worker’s model. Launch **workers in parallel** across independent slots when the host supports it; **within** each **(prompt, worker model, copy)** slot, run **worker** then **validator** **sequentially**. This repo does not call LLM APIs from Python.

## Preconditions

- Read [RESEARCH_PROTOCOL.md](../../research%20projects/RESEARCH_PROTOCOL.md) and [docs/ROLE_BINDING.md](../../research%20projects/docs/ROLE_BINDING.md).
- Read task-level `USER_PROMPT.md` (including **Approved search terms** and **Deliverable constraints**), `TODO.md`, `TOOLS_AND_MCP.md`, and hyperparameters — especially **`$ControlPlaneModel$`** and **`$ModelsForThisTask$`**.
- **Before the first worker delegation:** satisfy [Stage II readiness gates](../../research%20projects/RESEARCH_PROTOCOL.md#stage-ii-readiness-gates) and [Delegation requirement](../../research%20projects/RESEARCH_PROTOCOL.md#delegation-requirement). If any gate is unmet, **stop and ask**.
- Ensure `workers/` and `validators/` subfolders exist under this `{sub-task}`.

## Prompt variants (deduplication)

Generate and deduplicate prompt variants per [RESEARCH_PROTOCOL — Orchestrator algorithm step 1](../../research%20projects/RESEARCH_PROTOCOL.md#orchestrator-algorithm-per-subtask) using **`prompt_variants`** helpers ([Helper APIs](../../research%20projects/docs/SKILLS_AND_SCRIPTS.md#helper-apis)). Keep approved search terms in every variant.

## Fan-out pattern

For each **unique prompt** × **worker model** in **`$ModelsForThisTask$`** × **copy** `1..$WorkersPerTask$`, form a **slot**; parallelize **starting** workers across slots when the host allows.

1. **Worker:** `DELEGATION_PREAMBLE_WORKER` from [ROLE_BINDING](../../research%20projects/docs/ROLE_BINDING.md) + [research-worker/SKILL.md](../research-worker/SKILL.md). Set **`TASK_ROOT`** to this `{sub-task}/`’s parent (`outputs/.../{task-tldr}/`). Child runs on that slot’s **worker** model (not **`$ControlPlaneModel$`** unless also in the worker pool). Pass prompt, copy, output path `workers/worker-{model}-{copy}-{promptHash}.md` ([Filesystem structure](../../research%20projects/RESEARCH_PROTOCOL.md#filesystem-structure)), and `SHARED_CONTEXT.md` if present.
2. **Validator (same slot, after worker):** Launch on **`$ControlPlaneModel$`**. `DELEGATION_PREAMBLE_VALIDATOR` + [research-validator/SKILL.md](../research-validator/SKILL.md); same **`TASK_ROOT`**; output `validators/validator-{worker-model}-{copy}-{promptHash}.md`. Do not interleave validators ahead of unrelated workers.

Host isolation: [HOST_TOOLS](../../research%20projects/docs/HOST_TOOLS.md).

## Logging

- **Task-level `log_*.txt`:** append **START**/**END** pairs for `subtask`, `worker`, `validator`, and `host_subagent` events using **`execution_log`** helpers ([Helper APIs](../../research%20projects/docs/SKILLS_AND_SCRIPTS.md#helper-apis), [setup](../../research%20projects/docs/HOST_TOOLS.md#python)). Field contract: [RESEARCH_PROTOCOL — Execution log](../../research%20projects/RESEARCH_PROTOCOL.md#filesystem-structure).
- **Sub-task:** `orchestrator_log.md` (narrative, variants, worker/validator counts), `orchestrator_responses.md` (prompt → validated pairs), optional `orchestrator_meta.json`.

## Decision rules and propagation

- **Empty or ungrounded results:** **stop** and **ask the user** how to continue (new sources, narrower question).
- **Repetition:** generate **new unique** prompts (subject to **`$MaxCountToFindUniquePrompts$`** and, if set, **`$MaxOrchestratorIterations$`**).
- **Convergence:** if **no new information** appears across iterations, finish and mark the subtask complete in parent `TODO.md`.
- **In-subtask crucial facts:** when a worker surfaces something that **changes how remaining work in this `{sub-task}`** should proceed, append it to **`SHARED_CONTEXT.md`** (dated bullet list) so **new** delegated workers read it.
- **Related-work leads → replan:** when validated output implies **new subgoals outside** this subtask ([RESEARCH_PROTOCOL — Orchestrator algorithm](../../research%20projects/RESEARCH_PROTOCOL.md#orchestrator-algorithm-per-subtask) step 8), record the leads in **`orchestrator_log.md`**, mirror them to `SHARED_CONTEXT.md` only if they still inform this subtask’s remaining runs, and **ask the user** whether to run a **Stage I replan**. You **must not** edit **`TODO.md`** or **`TASK_GRAPH.json`** yourself ([docs/ROLE_BINDING.md](../../research%20projects/docs/ROLE_BINDING.md)).
- If propagation or escalation would **guess** user intent, **ask the user first**.

## Discovered skills

[Stage II reflection](../../research%20projects/docs/DISCOVERED_SKILLS_FLOW.md#stage-ii-reflection) (same as worker/validator) after primary outputs.
