# Skills and shared scripts

Where skills and Python helpers live, how to add them, and how they relate to the protocol. **Roles and delegation preambles:** [ROLE_BINDING.md](ROLE_BINDING.md). **Stages and filesystem layout:** [RESEARCH_PROTOCOL.md](../RESEARCH_PROTOCOL.md).

## Where skills live

- **Path:** `research projects/skills/<skill-name>/SKILL.md`
- **Frontmatter:** Each `SKILL.md` should include YAML `name` and `description` so hosts and humans can discover it.
- **Host-agnostic:** The protocol uses these project-local files. It does **not** depend on `.cursor/skills` or other editor-specific skill stores (though you may mirror content there if your host loads it).

## How to add or change a skill

1. If the change is **repeatable across tasks**, follow [research-skill-proposal/SKILL.md](../skills/research-skill-proposal/SKILL.md): evidence appendix, user approval, then implement.
2. Add or update `SKILL.md` under `research projects/skills/<name>/`.
3. If the skill is part of the **default protocol workflow** (Stage I, orchestration trio, or meta-skill for proposals), add or update a row in **Fundamental skills** below. **Ad-hoc** skills do not need to be listed there.

## Delegate deterministic work to Python

Prefer **shared helpers** for logic that should be stable and testable: normalization, deduplication keys, caps, parsing, and similar. Keep that behavior out of long prose in skills when a function is clearer. **Patterns:** skill markdown invokes `research_utils` (see [HOST_TOOLS.md](HOST_TOOLS.md#python) for `PYTHONPATH`); delegated children get preamble + skill path per [ROLE_BINDING.md](ROLE_BINDING.md).

## Where scripts live

- **Shared code:** `research projects/scripts/research_utils/` (import as `research_utils.*`).
- **Tests:** `research projects/scripts/tests/` (e.g. `test_*.py`).

Orchestrators should call these helpers instead of reimplementing string rules. **Concrete entry points** (canonical reference for names and usage):

<a id="helper-apis-research_utils"></a>

### Helper APIs (research_utils)

Caps and full workflow: [RESEARCH_PROTOCOL.md](../RESEARCH_PROTOCOL.md). Import path / pytest: [HOST_TOOLS.md](HOST_TOOLS.md#python).

- **`prompt_variants`:** `try_add_unique`, `collect_unique_prompts`, `prompt_fingerprint`, **`variant_collection_should_stop`** — [Stage II — step 1](../RESEARCH_PROTOCOL.md#orchestrator-algorithm-per-subtask).
- **`task_graph_waves`:** `execution_waves`, `topological_order`, `waves_from_task_graph_json` — [Stage I — step 6](../RESEARCH_PROTOCOL.md#planning-and-handoff); skill [research-task-graph-waves/SKILL.md](../skills/research-task-graph-waves/SKILL.md); CLI: `python -m research_utils.task_graph_waves`.
- **`execution_log`:** `resolve_task_execution_log`, `render_execution_record`, `append_execution_record` — task-level **`log_{datetime}.txt`** / **`execution_log_active.txt`** — [RESEARCH_PROTOCOL — `{task-tldr}`](../RESEARCH_PROTOCOL.md#filesystem-structure) (Execution log bullet).

## Tests and TDD

- **Requirement:** New or changed behavior under `scripts/` should come with **pytest** coverage in `research projects/scripts/tests/`.
- **Run, venv, `PYTHONPATH`:** [HOST_TOOLS.md](HOST_TOOLS.md#python) (paths and `pythonpath` in [pyproject.toml](../../pyproject.toml)).

## Fundamental skills (default workflow)

These are the **curated** skills that implement the default Stages I–II research roles and the process for extending the framework. Other skills may exist under `skills/` without being listed here until you promote them.

| Role / use | Skill |
|------------|--------|
| Stage I planning | [research-stage1-planning/SKILL.md](../skills/research-stage1-planning/SKILL.md) |
| Stage I task graph and waves | [research-task-graph-waves/SKILL.md](../skills/research-task-graph-waves/SKILL.md) |
| Orchestrator (one subtask) | [research-orchestrator/SKILL.md](../skills/research-orchestrator/SKILL.md) |
| Worker | [research-worker/SKILL.md](../skills/research-worker/SKILL.md) |
| Validator | [research-validator/SKILL.md](../skills/research-validator/SKILL.md) |
| Proposing new skills, scripts, or MCP | [research-skill-proposal/SKILL.md](../skills/research-skill-proposal/SKILL.md) |

For **which session may use which skill**, see [ROLE_BINDING.md](ROLE_BINDING.md). Repo index: [AGENTS.md](../../AGENTS.md).
