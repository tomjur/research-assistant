---
name: research-skill-proposal
description: >-
  Structures a user approval request before adding a new skill, script, or MCP
  based on observed repeatable behavior. Requires evidence appendix and self-review.
---

# Research — Skill / tool / MCP proposal

## When to use

- Any agent role (planning, orchestrator, worker, validator) notices behavior that could apply **across multiple** research tasks or domains.
- **Before** creating files under `research projects/skills/` (including any skill’s `scripts/`) or changing MCP config.

## When not to use

- One-off wording, a single paper’s quirks, or a unique user preference for **this** task only → log in `TODO.md` or orchestrator notes instead.

## Steps

1. **Draft evidence appendix** (in chat or `PROPOSAL_DRAFT.md` under the task folder):
   - **Example A** — concrete snippet / path / situation.
   - **Example B** — a second, independent instance.
   - **Why one-off fixes fail** — 2–3 sentences.
   - **Reuse plan** — where the skill would live (`research projects/skills/...`), trigger phrases, and what it would **not** cover.
2. **Re-read** the appendix. If you cannot honestly say “this will recur,” **stop** — no user question.
3. **Ask the user** with this structure:

   - **Proposal title**
   - **Change type**: new skill | new script | new MCP | extend existing
   - **Evidence appendix** (paste)
   - **Exact question**: “May I add this to the shared research framework?”

4. **Wait** for approval before writing shared assets.

## After approval

- Add or update `SKILL.md` under `research projects/skills/<name>/` with frontmatter `name` and `description`.
- If code: add `research projects/skills/<name>/scripts/<module>.py` and **tests** under `scripts/tests/`. Root [`conftest.py`](../../../conftest.py) adds every `skills/*/scripts` for pytest (see [docs/SKILLS_AND_SCRIPTS.md](../../docs/SKILLS_AND_SCRIPTS.md)).
- If the skill is part of the **default workflow**, add or update its row under **Fundamental skills** in [docs/SKILLS_AND_SCRIPTS.md](../../docs/SKILLS_AND_SCRIPTS.md).
