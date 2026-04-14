# Orchestrator scratchpad → split into artifacts

During the run, maintain:

- **Parent task dir** (`outputs/{research-project-x}/{task-tldr}/`) — task-level execution log: [RESEARCH_PROTOCOL — `{task-tldr}`](../RESEARCH_PROTOCOL.md#filesystem-structure); [Helper APIs — `execution_log`](../docs/SKILLS_AND_SCRIPTS.md#helper-apis). Append **`subtask`**, **`host_subagent`**, **`worker`**, and **`validator`** events with **START**/**END** pairs per that protocol section (not end-only).
- `orchestrator_log.md` — narrative log, prompts, worker counts
- `orchestrator_responses.md` — prompt / validated response pairs
- `orchestrator_meta.json` — optional JSON counters

## Subtask definition



## Prompt variants (unique)



## Run log

| Wave | Prompt hash | Model | Copy | Worker status | Validator status |
|------|-------------|-------|------|----------------|------------------|
| | | | | | |

## Findings tracker

<!--
Per-vendor accumulated atomic findings and round counters (see research-extract-atomic-findings
and research-compare-atomic-findings). Update after each round's validators return.
-->

### Vendor: `<model-slug>`

**Round counters:**

| Round | Slots launched | New findings | consecutive_no_new | Stopped |
|-------|----------------|--------------|---------------------|---------|
| | | | | |

**Accumulated findings:**

- <!-- atomic finding 1 (source: worker-<model>-<copy>-<hash>.md) -->

### Variant-level consolidated findings (after cross-vendor merge)

- <!-- finding present in all/any vendor's accumulated set -->

## Conflicts

<!-- Contradictory claims flagged by research-compare-atomic-findings. Surface to Stage III. -->

| Claim A | Claim B | Source A | Source B |
|---------|---------|----------|----------|
| | | | |

## Related-work leads

<!-- After each wave, record leads from validated output that imply new subgoals outside this subtask. Dedup against existing entries before adding. -->

| Lead summary | Source artifacts | Implies new subgoal | Escalated to user | Notes |
|---|---|---|---|---|
| | | | | |
