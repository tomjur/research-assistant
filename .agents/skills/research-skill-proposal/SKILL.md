---
name: research-skill-proposal
description: >-
  Implements an approved shared skill, script, or MCP change under .agents/skills/.
  Primary entry: after Stage III user approval per DISCOVERED_SKILLS_FLOW; secondary: explicit user request.
---

# Research — Skill / tool / MCP proposal

**Discovery pipeline:** [docs/DISCOVERED_SKILLS_FLOW.md](../../research%20projects/docs/DISCOVERED_SKILLS_FLOW.md). This skill = **implement** after Stage III approval or an **explicit** user request (not routine Stage II asks).

## When to use

- **Primary:** User approved a candidate in [Stage III consolidation](../../research%20projects/docs/DISCOVERED_SKILLS_FLOW.md#stage-iii-consolidation).
- **Secondary:** User explicitly asked for a shared skill/script/MCP change outside that flow.

Do **not** edit `.agents/skills/` (or MCP config) without that approval.

## When not to use

- Task-only quirks → `TODO.md` / orchestrator notes.
- Stage II drafting only → [Stage II reflection](../../research%20projects/docs/DISCOVERED_SKILLS_FLOW.md#stage-ii-reflection), not this skill.

## Before implementing

1. Evidence: use approved draft from `discovered-skills/` / `APPROVAL_LOG.md` (add appendix if missing: two instances, why not one-off, reuse plan).
2. **Change type:** new skill | new script | new MCP | extend existing.

## Implementation (after approval)

- Add or update `SKILL.md` under `.agents/skills/<name>/` with frontmatter `name` and `description`.
- If code: add `.agents/skills/<name>/scripts/<module>.py` and **tests** under `scripts/tests/`. Root [`conftest.py`](../../../conftest.py) adds every `skills/*/scripts` for pytest (see [docs/SKILLS_AND_SCRIPTS.md](../../research%20projects/docs/SKILLS_AND_SCRIPTS.md)).
- If the skill is part of the **default workflow**, add or update its row under **Fundamental skills** in [docs/SKILLS_AND_SCRIPTS.md](../../research%20projects/docs/SKILLS_AND_SCRIPTS.md).
