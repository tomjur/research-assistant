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

## Fan-out pattern (round-based, per prompt variant)

For each **unique prompt**, dispatch workers in **rounds** until all vendors in **`$ModelsForThisTask$`** are stopped or have hit the **`$WorkersPerTask$`** cap. Per-vendor state carried across rounds: `accumulated_findings_V` (set), `consecutive_no_new_V` (int), `launched_V` (int).

**Per round:**

1. **Slot calculation (per vendor V):**
   ```
   slots_V = max(0, $EarlyStoppingWorkers$ − consecutive_no_new_V)
   slots_V = min(slots_V, $WorkersPerTask$ − launched_V)   # respect total cap
   ```
   Copy indices for the round: `launched_V + 1 .. launched_V + slots_V`.
2. **Launch workers in parallel** across every `(vendor V, copy c)` slot with `slots_V > 0`. Worker delegation: `DELEGATION_PREAMBLE_WORKER` from [ROLE_BINDING](../../research%20projects/docs/ROLE_BINDING.md) + [research-worker/SKILL.md](../research-worker/SKILL.md). Set **`TASK_ROOT`** to this `{sub-task}/`’s parent. Output path: `workers/worker-{model}-{copy}-{promptHash}.md`. Pass `SHARED_CONTEXT.md` if present.
3. **Validator per slot (sequential after its worker):** Launch on **`$ControlPlaneModel$`**. `DELEGATION_PREAMBLE_VALIDATOR` + [research-validator/SKILL.md](../research-validator/SKILL.md); output `validators/validator-{worker-model}-{copy}-{promptHash}.md`. Do not interleave validators ahead of unrelated workers.
4. **Update per-vendor state** (only after all round validators return). For each vendor V, process its slots in **copy-index order**:
   - Run `extract` ([research-extract-atomic-findings](../research-extract-atomic-findings/SKILL.md)) on the validated output → `new_items`.
   - If `accumulated_findings_V` is empty: `accumulated_findings_V ← new_items`, `consecutive_no_new_V ← 0`.
   - Else run the **Merge procedure** (below) with `A = accumulated_findings_V`, `B = new_items`:
     - If `|only_B| ≥ 1`: `accumulated_findings_V ← accumulated_findings_V ∪ only_B`, `consecutive_no_new_V ← 0`.
     - Else: `consecutive_no_new_V ← consecutive_no_new_V + 1`.
   - Increment `launched_V`.
5. **Stop per vendor** when `consecutive_no_new_V ≥ $EarlyStoppingWorkers$` OR `launched_V ≥ $WorkersPerTask$`.
6. **Stop the prompt variant** when every vendor is stopped.

After the prompt variant finishes: run **Merge** across vendors (site #2, see below) to build the variant-level consolidated findings set.

Host isolation: [HOST_TOOLS](../../research%20projects/docs/HOST_TOOLS.md).

## Comparing validated outputs (Merge procedure)

Reduces "compare two texts for overlapping information" to set operations on atomic findings. Used at three sites:

| Site | A | B | Use of result |
|------|---|---|----------------|
| Same vendor, between rounds | `accumulated_findings_V` | new validated output N+1 for vendor V | `\|only_B\|` drives `consecutive_no_new_V` |
| Cross-vendor within a prompt variant | vendor A's accumulated set | vendor B's accumulated set | build variant-level consolidated findings; flag conflicts |
| Cross-prompt-variant (convergence) | variant 1's consolidated findings | variant 2's consolidated findings | drives RESEARCH_PROTOCOL step 5/6 convergence |

**Procedure:**

1. Extract: run [research-extract-atomic-findings](../research-extract-atomic-findings/SKILL.md) on each of text A, text B → `items_A`, `items_B`. (Skip if the input is already an atomic-findings set.)
2. Compare A→B: run [research-compare-atomic-findings](../research-compare-atomic-findings/SKILL.md) with `(items_A, items_B)`.
3. Compare B→A: run [research-compare-atomic-findings](../research-compare-atomic-findings/SKILL.md) with `(items_B, items_A)`.
4. Partition:
   - `only_A` = A-side items with `match_in_B = no`
   - `only_B` = B-side items with `match_in_A = no`
   - `common` = A-side items with `match_in_B = yes` (cross-check with B-side matched set)
5. **Disagreement check:** if the two calls disagree on the size of `common`, default to the **conservative union** (treat weakly-matched items as `only_*` rather than `common`). Flag the disagreement in `orchestrator_log.md`.

**Conflicts:** items flagged `contradicts-B` by the compare skill become part of `only_A` (or `only_B`). Record them in `orchestrator_log.md` under `## Conflicts` so Stage III can surface them.

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
  - `atomic_extraction` — after running [research-extract-atomic-findings](../research-extract-atomic-findings/SKILL.md). Fields: `source_artifact` (path to validator file or equivalent), `item_count` (integer).
  - `atomic_compare` — after each directional call to [research-compare-atomic-findings](../research-compare-atomic-findings/SKILL.md). Fields: `direction` (`A_to_B` | `B_to_A`), `site` (`same_vendor` | `cross_vendor` | `cross_variant`), `a_count`, `b_count`, `match_count`, `only_a_count`, `only_b_count`.
  - `early_stopping_round` — once per round after state updates. Fields: `prompt_variant_hash`, `round` (integer), per-vendor summary: `vendor`, `slots_launched`, `new_findings_count`, `consecutive_no_new`, `vendor_stopped` (`yes` | `no`). Emit one `early_stopping_round` block per vendor per round, or a single block with a multiline `per_vendor` summary.
- **Sub-task:** `orchestrator_log.md` (narrative, variants, worker/validator counts, **`## Related-work leads`** section, **`## Findings tracker`** with per-vendor accumulated atomic findings + round-by-round counts, optional **`## Conflicts`**), `orchestrator_responses.md` (prompt → validated pairs), optional `orchestrator_meta.json`.

## Decision rules and propagation

- **Empty or ungrounded results:** **stop** and **ask the user** how to continue (new sources, narrower question).
- **Repetition:** generate **new unique** prompts (subject to **`$MaxCountToFindUniquePrompts$`** and, if set, **`$MaxOrchestratorIterations$`**).
- **Early stopping (per vendor, within a prompt variant):** a vendor stops when its `consecutive_no_new` counter reaches **`$EarlyStoppingWorkers$`** or it has launched **`$WorkersPerTask$`** workers. Driven by the Merge procedure on successive validated outputs from the same vendor.
- **Convergence (across prompt variants):** if **no new information** appears across iterations (measured via the Merge procedure applied to variant-level consolidated findings), finish and mark the subtask complete in parent `TODO.md`. This is **orthogonal** to per-vendor early stopping — early stopping short-circuits within a variant; convergence decides whether to launch another variant.
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
