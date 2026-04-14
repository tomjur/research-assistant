---
name: research-extract-atomic-findings
description: >-
  Extracts a list of atomic factual items from a given text, grounded strictly in
  the text (no inference, no world knowledge). Used by the orchestrator to reduce
  "compare two texts" to "compare two sets of strings by meaning". Paired with
  research-compare-atomic-findings.
---

# Research — Extract atomic findings

## When to use

- **Invoked by:** the orchestrator (`$ControlPlaneModel$`), as an inline procedure — not a delegated child.
- **Purpose:** reduce a validated worker response (or any text block) to a flat list of atomic factual claims, so comparisons can be done as set operations on strings by meaning.
- **Pairs with:** [research-compare-atomic-findings](../research-compare-atomic-findings/SKILL.md).

## Input

- A text block. The canonical case is the `## Validated response` body of one `validators/validator-*.md` artifact. Any prose/structured text is valid input.

## Output

An ordered list where each item is one atomic finding. Format per line:

```
- <claim>  (source: "<short quote or line range>")
```

- **One claim per bullet.** No compound sentences — split `A and B` into two findings.
- **Declarative active voice.** "RepoBench evaluates retrieval and completion tasks" not "It was evaluated that...".
- **Preserve specific details verbatim:** numbers, model names, dates, identifiers, URLs.
- **Strip source attribution wording from the claim itself.** "The paper says X" → "X"; record the source pointer in the trailing `(source: ...)`.
- **Audit pointer:** every finding must carry a pointer back to the source span so a reviewer can verify it is grounded.

## Grounding rules (critical)

- **Only what the text explicitly states.** If the input does not state a claim, do **not** emit it. No "obvious" inferences, no world-knowledge fill-in, no LLM imagination.
- **Preserve explicit uncertainty.** If the source says "may", "appears", "estimated", keep that hedge in the finding ("X may cause Y" — do not strengthen to "X causes Y").
- **Split compound statements.** "The benchmark covers 1,099 instances across 18 projects" → two findings: "The benchmark covers 1,099 instances." and "The benchmark covers 18 projects."
- **Contradictions within the source become two findings**, both preserved. Flag neither as wrong — the extractor does not adjudicate truth.
- **Do not emit meta-commentary** (e.g., "The response is well-sourced"). Only substantive factual claims.
- **Do not introduce citations or URLs not present in the source.**

## Examples

### Example 1 — grounded

**Input:**
```
RepoBench (arXiv:2306.03091) defines three tasks — RepoBench-R (retrieval),
RepoBench-C (completion), RepoBench-P (pipeline combining both) — evaluated on
Python and Java repositories. Code is available at Leolty/repobench.
```

**Output:**
```
- RepoBench is described at arXiv:2306.03091.  (source: "RepoBench (arXiv:2306.03091)")
- RepoBench defines three tasks.  (source: "defines three tasks")
- RepoBench-R is a retrieval task.  (source: "RepoBench-R (retrieval)")
- RepoBench-C is a completion task.  (source: "RepoBench-C (completion)")
- RepoBench-P is a pipeline task combining retrieval and completion.  (source: "RepoBench-P (pipeline combining both)")
- RepoBench is evaluated on Python repositories.  (source: "Python and Java repositories")
- RepoBench is evaluated on Java repositories.  (source: "Python and Java repositories")
- RepoBench code is available at Leolty/repobench.  (source: "Leolty/repobench")
```

### Example 2 — what NOT to emit

**Input:** same as Example 1.

**Do not emit:**
- ❌ "RepoBench is a well-known benchmark in the field."  *(meta-commentary, not in text)*
- ❌ "RepoBench was published in 2023."  *(inferred from arXiv ID prefix — source does not explicitly state year)*
- ❌ "RepoBench is better than SWE-bench."  *(comparative judgment not in text)*
- ❌ "RepoBench uses transformer models."  *(world knowledge not in text)*

### Example 3 — preserving hedges and contradictions

**Input:**
```
Community writeups suggest ReCUBE-style stress tests may approximate
real-world repair difficulty, though the primary paper has not been located
in this task.
```

**Output:**
```
- ReCUBE-style stress tests may approximate real-world repair difficulty (per community writeups).  (source: "may approximate real-world repair difficulty")
- The primary ReCUBE paper has not been located in this task.  (source: "the primary paper has not been located in this task")
```

Note the hedge "may" is preserved, and the gap is emitted as its own finding.

## Invocation contract

- The orchestrator calls this skill on each validated output that enters a comparison.
- Output is stored in `orchestrator_log.md` under `## Findings tracker` for auditability (per-vendor section).
- Log a `step` event with action `atomic_extraction`, fields: `source_artifact` (path), `item_count` (integer). See [research-orchestrator/SKILL.md](../research-orchestrator/SKILL.md#logging).

## What this skill does NOT do

- Does **not** compare two sets — see [research-compare-atomic-findings](../research-compare-atomic-findings/SKILL.md).
- Does **not** validate or fact-check — that is the validator's job upstream.
- Does **not** resolve contradictions — downstream merge logic decides.
- Does **not** delegate to child agents — runs inline in the orchestrator session.
