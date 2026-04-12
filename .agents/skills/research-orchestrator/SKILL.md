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

- **Task-level `log_*.txt`:** Use **`log_event`** for START blocks and **`log_end_event`** for END blocks (both generate timestamps at write-time and `log_end_event` auto-computes `duration_s`). Append `subtask`, `worker`, `validator`, and `host_subagent` events. Field contract: [RESEARCH_PROTOCOL — Execution log](../../research%20projects/RESEARCH_PROTOCOL.md#filesystem-structure). Setup: [Helper APIs](../../research%20projects/docs/SKILLS_AND_SCRIPTS.md#helper-apis), [HOST_TOOLS](../../research%20projects/docs/HOST_TOOLS.md#python).
- **`delegation_type`** (**required** on worker/validator START): record how the child was launched — `host_subagent` | `background_agent` | `inline_single_session` | other host-specific string.
- **Validator END extras:** include `claims_challenged` and `links_checked` when available.
- **Step events:** Use **`log_step`** (or manual `step` blocks) for discrete actions **within** this subtask:
  - `skill_invocation` — when opening `research-worker` or `research-validator` SKILL.md for a delegation.
  - `script_call` — when calling `prompt_variants` or `execution_log` helpers.
  - `prompt_variant_collection` — after dedup, with `candidates_generated`, `unique_accepted`, `duplicates_rejected`, `stop_reason`.
  - `user_decision` — when escalating to the user (replan, empty results, scope question) and recording their answer. When asking about a replan triggered by related-work leads, reference the specific leads by `lead_summary`.
  - `related_work_lead` — when the orchestrator identifies a substantive lead from validated output. Fields: `lead_summary`, `source_artifacts`, `implies_new_subgoal`, `escalated_to_user`, optional `dedup_note`. See [RESEARCH_PROTOCOL — Execution log](../../research%20projects/RESEARCH_PROTOCOL.md#filesystem-structure).
- **Sub-task:** `orchestrator_log.md` (narrative, variants, worker/validator counts, **`## Related-work leads`** section), `orchestrator_responses.md` (prompt → validated pairs), optional `orchestrator_meta.json`.

## Decision rules and propagation

- **Empty or ungrounded results:** **stop** and **ask the user** how to continue (new sources, narrower question).
- **Repetition:** generate **new unique** prompts (subject to **`$MaxCountToFindUniquePrompts$`** and, if set, **`$MaxOrchestratorIterations$`**).
- **Convergence:** if **no new information** appears across iterations, finish and mark the subtask complete in parent `TODO.md`.
- **In-subtask crucial facts:** when a worker surfaces something that **changes how remaining work in this `{sub-task}`** should proceed, append it to **`SHARED_CONTEXT.md`** (dated bullet list) so **new** delegated workers read it.
- **Related-work leads → replan:** after each validator completes, scan the validated output for leads from related-work or equivalent sections that imply **new subgoals outside** this subtask ([RESEARCH_PROTOCOL — Orchestrator algorithm](../../research%20projects/RESEARCH_PROTOCOL.md#orchestrator-algorithm-per-subtask) step 8). For each lead:
  1. **Check `## Related-work leads`** in `orchestrator_log.md` — if a substantially similar lead is already recorded, note it as corroborating evidence on the existing entry (update `source_artifacts`) rather than creating a duplicate. Log a `related_work_lead` step event with `dedup_note`.
  2. If the lead is **net-new**, add it to `## Related-work leads` with: short description, source artifact(s), whether it implies a new subgoal. Log a `related_work_lead` step event.
  3. Mirror to `SHARED_CONTEXT.md` only if the lead still informs this subtask’s remaining runs.
  4. **Batch escalation:** after a full wave of workers/validators completes (not after each individual worker), collect all net-new leads that imply new subgoals and **ask the user once** whether to run a Stage I replan. Log a `user_decision` step event referencing the specific leads. Do **not** re-escalate leads the user has already seen.
  5. You **must not** edit **`TODO.md`** or **`TASK_GRAPH.json`** yourself ([docs/ROLE_BINDING.md](../../research%20projects/docs/ROLE_BINDING.md)).
- If propagation or escalation would **guess** user intent, **ask the user first**.

## Discovered skills

[Stage II reflection](../../research%20projects/docs/DISCOVERED_SKILLS_FLOW.md#stage-ii-reflection) (same as worker/validator) after primary outputs.
