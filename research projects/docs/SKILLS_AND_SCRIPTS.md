# Skills and scripts

Where skills and Python helpers live, how to add them, and how they relate to the protocol.

## Where skills live

- **Path:** `.agents/skills/<skill-name>/SKILL.md` (at the repo root)
- **Frontmatter:** Each `SKILL.md` should include YAML `name` and `description` so hosts and humans can discover it.
- **Host-agnostic:** `.agents/skills/` is natively read by Cursor, Gemini CLI, and OpenCode. Claude Code discovers skills via a `.claude/skills` → `.agents/skills` symlink.

## How to add or change a skill

1. Repeatable across tasks: [DISCOVERED_SKILLS_FLOW](DISCOVERED_SKILLS_FLOW.md) ([Stage II](DISCOVERED_SKILLS_FLOW.md#stage-ii-reflection) → [Stage III](DISCOVERED_SKILLS_FLOW.md#stage-iii-consolidation) → [research-skill-proposal](../../.agents/skills/research-skill-proposal/SKILL.md)). Out-of-band: **research-skill-proposal** after explicit user approval only.
2. Add or update `SKILL.md` under `.agents/skills/<name>/`.
3. If the skill is part of the **default protocol workflow** (Stage I, orchestration trio, or meta-skill for proposals), add or update a row in **Fundamental skills** below. **Ad-hoc** skills do not need to be listed there.

## Delegate deterministic work to Python

Prefer **helpers** for logic that should be stable and testable (normalization, deduplication, caps, parsing). Import top-level modules by name (e.g. `task_graph_waves`, `prompt_variants`) after setting `PYTHONPATH` per [HOST_TOOLS.md](HOST_TOOLS.md#python). Delegated children get preamble + skill path per [ROLE_BINDING.md](ROLE_BINDING.md).

## Where scripts live

Helpers are **`.agents/skills/<skill-name>/scripts/<module>.py`**; tests in **`scripts/tests/test_*.py`**. **pytest** prepends every `skills/*/scripts` via root [`conftest.py`](../../conftest.py). For ad hoc Python, set `PYTHONPATH` to those same dirs (see [HOST_TOOLS.md](HOST_TOOLS.md#python)).

<a id="helper-apis"></a>

### Helper APIs

Caps and workflow: [RESEARCH_PROTOCOL.md](../RESEARCH_PROTOCOL.md). Run / import: [HOST_TOOLS.md](HOST_TOOLS.md#python).

- **`prompt_variants`:** `try_add_unique`, `collect_unique_prompts`, `prompt_fingerprint`, **`variant_collection_should_stop`** — [Stage II — step 1](../RESEARCH_PROTOCOL.md#orchestrator-algorithm-per-subtask); [orchestrator `scripts/`](../../.agents/skills/research-orchestrator/scripts/).
- **`task_graph_waves`:** `execution_waves`, `topological_order`, `waves_from_task_graph_json` — [Stage I — step 6](../RESEARCH_PROTOCOL.md#planning-and-handoff); [research-task-graph-waves/SKILL.md](../../.agents/skills/research-task-graph-waves/SKILL.md); CLI: `python -m task_graph_waves --file path/to/TASK_GRAPH.json`.
- **`execution_log`:** `resolve_task_execution_log`, `render_execution_record`, `append_execution_record`, `format_log_filename`, `CANONICAL_LOG_PATTERN`, `utc_timestamp_iso`, `ExecutionLogRole` — task-level **`log_YYYY-MM-DD_HHMMSS.txt`** (UTC) in **`outputs/{research-project-x}/{task-tldr}/`**. **`render_execution_record`** roles: `worker`, `validator`, `planning`, `subtask`, `host_subagent` — [RESEARCH_PROTOCOL — Filesystem structure](../RESEARCH_PROTOCOL.md#filesystem-structure); [orchestrator `scripts/`](../../.agents/skills/research-orchestrator/scripts/).

## Tests and TDD

New or changed `scripts/*.py` behavior needs **pytest** under that skill’s `scripts/tests/`. Collection is recursive under `.agents/skills/` ([`pyproject.toml`](../../pyproject.toml)); paths come from [`conftest.py`](../../conftest.py).

## Fundamental skills (default workflow)

| Role / use | Skill |
|------------|--------|
| Stage I planning | [research-stage1-planning/SKILL.md](../../.agents/skills/research-stage1-planning/SKILL.md) |
| Stage I task graph and waves | [research-task-graph-waves/SKILL.md](../../.agents/skills/research-task-graph-waves/SKILL.md) |
| Orchestrator (one subtask) | [research-orchestrator/SKILL.md](../../.agents/skills/research-orchestrator/SKILL.md) |
| Worker | [research-worker/SKILL.md](../../.agents/skills/research-worker/SKILL.md) |
| Validator | [research-validator/SKILL.md](../../.agents/skills/research-validator/SKILL.md) |
| Implementing approved skills, scripts, or MCP (after Stage III or explicit user request) | [research-skill-proposal/SKILL.md](../../.agents/skills/research-skill-proposal/SKILL.md) |

For **which session may use which skill**, see [ROLE_BINDING.md](ROLE_BINDING.md). Repo index: [AGENTS.md](../../AGENTS.md).
