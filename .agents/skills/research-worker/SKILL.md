---
name: research-worker
description: >-
  Executes one research assignment for a fixed prompt variant and model: structured
  answer with citations and links. Writes worker artifact markdown; does not validate links.
---

# Research — Worker

## When to use

- Invoked by an orchestrator for one **(prompt variant, model, copy)** run.
- **Read-only** regarding validation: you produce a **draft**; the validator grounds it.

## Inputs (orchestrator provides)

- Exact **prompt** (do not shorten unless the orchestrator instructed a shorter variant).
- **Worker model** slug from **`$ModelsForThisTask$`** (record as metadata; the **host** must run this delegated session with that model, not the orchestrator’s **`$ControlPlaneModel$`** unless they are the same ID by user choice).
- **Copy** index (integer).
- Output path: `workers/worker-{model}-{copy}-{promptHash}.md`
- Optional: `SHARED_CONTEXT.md` from the subtask folder — fold relevant facts into the answer.
- Task-level **`USER_PROMPT.md`** (or the orchestrator message): if **Deliverable constraints** specify length/depth or per-worker draft limits, apply them to the **Response** body (Summary, Findings, etc.).

## Output shape

Use the canonical layout in [templates/worker.example.md](../../research%20projects/templates/worker.example.md) (front matter + **Prompt** + **Response** sections).

## Rules

- **Length:** **`USER_PROMPT.md`** **Deliverable constraints** (or orchestrator message).
- **Sources:** Prefer primary / official / peer-reviewed when appropriate; every non-obvious claim → **Sources** or **Gaps / uncertainty**.
- **Related-work sections:** Extract **sourced** leads (Related work, Background, Bibliography, etc.); put out-of-scope but mission-relevant leads in **Gaps / uncertainty** so the orchestrator can escalate or propagate them.
- **Links:** Do **not** claim HTTP verification unless you fetched; validator checks.
- **Discovered skills:** After primary artifact, [Stage II reflection](../../research%20projects/docs/DISCOVERED_SKILLS_FLOW.md#stage-ii-reflection).

## After writing

- Tell the orchestrator the artifact path so it can launch the **validator** on this file.
