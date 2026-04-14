---
name: research-compare-atomic-findings
description: >-
  Directional semantic comparison of two atomic-finding sets. Given set A and set B,
  reports for each item in A whether it has a match in B by meaning (not verbatim).
  Called twice with swapped arguments to derive only_A / only_B / common.
  Used by the orchestrator to merge results across workers, vendors, and prompt variants.
---

# Research — Compare atomic findings

## When to use

- **Invoked by:** the orchestrator (`$ControlPlaneModel$`), as an inline procedure — not a delegated child.
- **Purpose:** given two sets of atomic findings, decide by meaning which items of A are also present in B (and which are new).
- **Pairs with:** [research-extract-atomic-findings](../research-extract-atomic-findings/SKILL.md) — always run extraction first on the source texts before comparing.

## Input

- **`items_A`**: a list of atomic findings (typically the output of [research-extract-atomic-findings](../research-extract-atomic-findings/SKILL.md) on text A).
- **`items_B`**: a list of atomic findings (same format, from text B).

## Output

For **each** item in A, one record:

```
- <item_A_text>
  match_in_B: yes | no
  matched_B_item: <item_B_text>   # only if match_in_B = yes
  reason: truly-new | contradicts-B | adjacent-but-distinct   # only if match_in_B = no
```

Plus a summary footer:

```
totals: a_count=<N_A>, b_count=<N_B>, match_count=<M>, only_a_count=<N_A - M>
```

## Comparison rules

- **Match by meaning, not verbatim.** Paraphrases, synonym substitutions, reordered clauses that convey the **same factual content** → match.
  - "RepoBench-R is a retrieval task" ≡ "The retrieval task in RepoBench is called RepoBench-R" → match.
- **Contradictions are NOT matches.** If A claims X and B claims ¬X, the A item's `reason` is `contradicts-B` (and it will end up in `only_A`). The orchestrator handles conflicts downstream.
- **Partial overlap is NOT a match.**
  - If A says "SWE-Refactor contains 922 atomic refactorings" and B says "SWE-Refactor contains 1,099 refactorings" — these are distinct facts, not a match. The more specific one is additional information.
  - If A strictly subsumes B (e.g., A="contains 1,099 instances from 18 Java projects", B="contains 1,099 instances"), A is not "in B" — it has extra content. Mark `adjacent-but-distinct`.
- **Conservative default.** When genuinely ambiguous, mark as **no-match** with `adjacent-but-distinct`. It is safer to over-report novelty than to under-report.
- **Identifier-level details matter.** Different version numbers, different dataset sizes, different model slugs ⇒ not a match.
- **Same claim about different entities is NOT a match.** "Python repos are evaluated" vs "Java repos are evaluated" are distinct.

## Examples

### Example 1 — paraphrase match

```
items_A:
- RepoBench defines three tasks.
- RepoBench-C is a completion task.

items_B:
- RepoBench has three tasks: retrieval, completion, and pipeline.
- The completion task in RepoBench is called RepoBench-C.
```

**Output:**
```
- RepoBench defines three tasks.
  match_in_B: yes
  matched_B_item: RepoBench has three tasks: retrieval, completion, and pipeline.
- RepoBench-C is a completion task.
  match_in_B: yes
  matched_B_item: The completion task in RepoBench is called RepoBench-C.

totals: a_count=2, b_count=2, match_count=2, only_a_count=0
```

### Example 2 — contradiction

```
items_A:
- SWE-Refactor contains 1,099 instances.

items_B:
- SWE-Refactor contains 950 instances.
```

**Output:**
```
- SWE-Refactor contains 1,099 instances.
  match_in_B: no
  reason: contradicts-B

totals: a_count=1, b_count=1, match_count=0, only_a_count=1
```

Both items end up in `only_X` (after the symmetric call). The orchestrator should note the conflict.

### Example 3 — adjacent-but-distinct

```
items_A:
- CodeTaste mines multi-file refactor tasks from OSS projects.

items_B:
- CodeTaste uses tests and static checks to score agents.
```

**Output:**
```
- CodeTaste mines multi-file refactor tasks from OSS projects.
  match_in_B: no
  reason: adjacent-but-distinct

totals: a_count=1, b_count=1, match_count=0, only_a_count=1
```

Both talk about CodeTaste but state different facts — no match.

## Invocation contract

- **Always call twice** with swapped arguments to get the full partition:
  - Call 1: `compare(items_A, items_B)` → A-side records.
  - Call 2: `compare(items_B, items_A)` → B-side records.
- The orchestrator then derives:
  - `only_A` = A items with `match_in_B = no`
  - `only_B` = B items with `match_in_A = no`
  - `common` = A items with `match_in_B = yes` (cross-check against call 2's matched set; on disagreement use the conservative union — treat weakly matched items as `only_*` rather than `common`).
- Log each call as a `step` event with action `atomic_compare`, fields: `direction` (A→B / B→A), `site` (same_vendor / cross_vendor / cross_variant), `a_count`, `b_count`, `match_count`, `only_a_count`, `only_b_count`. See [research-orchestrator/SKILL.md](../research-orchestrator/SKILL.md#logging).

## What this skill does NOT do

- Does **not** extract findings from raw text — first run [research-extract-atomic-findings](../research-extract-atomic-findings/SKILL.md).
- Does **not** produce the final partition by itself — the orchestrator combines two calls.
- Does **not** resolve contradictions or rank claims by trustworthiness.
- Does **not** delegate to child agents — runs inline in the orchestrator session.
