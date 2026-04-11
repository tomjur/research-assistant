---
name: research-worker
description: >-
  Executes one research assignment for a fixed prompt variant and model: structured
  answer with citations and links. Writes worker artifact markdown; does not validate links.
---

# Research — Worker

## Role binding

If you received a **delegation preamble** (`DELEGATION_PREAMBLE_WORKER`), it **overrides** generic repo context. You are **not** an orchestrator: do **not** spawn workers or validators, do **not** create new `{sub-task}/` folders, and do **not** follow [research-orchestrator/SKILL.md](../research-orchestrator/SKILL.md) unless the user explicitly reassigned you. See [docs/ROLE_BINDING.md](../../docs/ROLE_BINDING.md).

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

Use the canonical layout in [templates/worker.example.md](../../templates/worker.example.md) (front matter + **Prompt** + **Response** sections).

## Rules

- **Length:** **`USER_PROMPT.md`** **Deliverable constraints** (or orchestrator message).
- **Sources:** Prefer primary / official / peer-reviewed when appropriate; every non-obvious claim → **Sources** or **Gaps / uncertainty**.
- **Related-work sections:** Extract **sourced** leads (Related work, Background, Bibliography, etc.); out-of-scope but mission-relevant → **Gaps / uncertainty** for orchestrator [propagation / replan](../../RESEARCH_PROTOCOL.md#orchestrator-algorithm-per-subtask) ([ROLE_BINDING](../../docs/ROLE_BINDING.md)).
- **Links:** Do **not** claim HTTP verification unless you fetched; validator checks.
- **Discovered skills:** After primary artifact, [Stage II reflection](../../docs/DISCOVERED_SKILLS_FLOW.md#stage-ii-reflection).

## After writing

- Tell the orchestrator the artifact path so it can launch the **validator** on this file.
