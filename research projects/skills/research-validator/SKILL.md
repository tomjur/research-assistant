---
name: research-validator
description: >-
  Skeptically validates a single worker research artifact: stress-test the draft for faults,
  check links and sources where possible, remove or flag ungrounded claims, edit the response,
  write validator artifact. Does not perform new open-ended research.
---

# Research — Validator

## Role binding

If you received **DELEGATION_PREAMBLE_VALIDATOR**, it **overrides** generic repo context. You are **not** an orchestrator or a research worker for **new** topics: do **not** delegate, do **not** spawn workers, and do **not** run open-ended fresh research. See [docs/ROLE_BINDING.md](../../docs/ROLE_BINDING.md).

## When to use

- Immediately **after** a worker writes `workers/worker-{model}-{copy}-{promptHash}.md`.
- One validator run **per** worker artifact.

## Inputs

- Path to the worker markdown file.
- You run on **`$ControlPlaneModel$`** (same as orchestrator). The **host** must use that model for **this** delegated session, **not** the worker’s model.
- **Copy** / **prompt** metadata and **worker** model slug: read from the worker file front matter (orchestrator message should match `DELEGATION_PREAMBLE_VALIDATOR`).
- Output path: `validators/validator-{worker-model-slug}-{copy}-{promptHash}.md` (slug in the filename is the **worker** draft’s model, for pairing with `workers/worker-...`.md).

## Verification stance

Align with **VERIFICATION_STANCE** in [`DELEGATION_PREAMBLE_VALIDATOR`](../../docs/ROLE_BINDING.md#delegation-preamble-validator) (fault-finding by **editing/grounding** this artifact only; preserve well-cited **related-work** leads; flag unverified).

## What you do

1. **Read** the worker file.
2. For each **URL** in `Sources` (and inline links):
   - When tools/network are available, **verify** reachability and that the page content **supports** the cited claim.
   - If you cannot verify, **mark** the claim as unverified or remove it from the validated narrative.
3. **Edit** the worker’s `## Response` body into a **validated** version:
   - Remove hallucinated citations.
   - Soften or delete claims without evidence.
   - **Do not strip** well-cited **related-work follow-up leads** (e.g. pointers from a paper’s related-work section) solely because they resemble “new research”—tighten wording, flag anything you could not verify, but **preserve** structured leads that remain tied to **Sources**.
   - Keep structure parallel to the worker where possible.
4. Append a **Validator changelog** section listing edits (bullet list).

## What you must not do

- Do **not** replace the task with fresh research or new topics.
- Do **not** invent new URLs.
- Do **not** orchestrate further workers or validators.

## Output shape

Use [templates/validator.example.md](../../templates/validator.example.md) (front matter, **Validated response**, **Validator changelog**, **Grounding notes**).

After the validator artifact is written: [Stage II reflection](../../docs/DISCOVERED_SKILLS_FLOW.md#stage-ii-reflection).

## Failure path

- If **nothing** can be grounded (`validation_status: failed`), still write the file and return a concise reason list so the orchestrator can **ask the user** next steps.
