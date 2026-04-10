# Task templates

Copy files from this folder when starting `research projects/{project}/{task-tldr}/` and each `{sub-task}/`.

| Template | Target location |
|----------|-----------------|
| [USER_PROMPT.md](USER_PROMPT.md) | `{task-tldr}/USER_PROMPT.md` |
| (at Stage II) | Task-level log: [RESEARCH_PROTOCOL — `{task-tldr}`](../RESEARCH_PROTOCOL.md#filesystem-structure) (Execution log bullet); [Helper APIs](../docs/SKILLS_AND_SCRIPTS.md#helper-apis-research_utils) |
| [TODO.md](TODO.md) | `{task-tldr}/TODO.md` |
| [TOOLS_AND_MCP.md](TOOLS_AND_MCP.md) | `{task-tldr}/TOOLS_AND_MCP.md` |
| [HYPERPARAMETERS.md](HYPERPARAMETERS.md) | `{task-tldr}/HYPERPARAMETERS.md` (optional if merged into tools doc) |
| [FINAL_RESPONSE.md](FINAL_RESPONSE.md) | `{task-tldr}/FINAL_RESPONSE.md` (fill at end) |
| [SUBTASK_ORCHESTRATOR.md](SUBTASK_ORCHESTRATOR.md) | `{sub-task}/` — rename/split into `orchestrator_log.md`, `orchestrator_responses.md`, `orchestrator_meta.json` as you go |
| [SHARED_CONTEXT.md](SHARED_CONTEXT.md) | `{sub-task}/SHARED_CONTEXT.md` |
| [worker.example.md](worker.example.md) | `{sub-task}/workers/worker-{model}-{copy}-{promptHash}.md` |
| [validator.example.md](validator.example.md) | `{sub-task}/validators/validator-{model}-{copy}-{promptHash}.md` |

**Worker/validator filenames and `promptHash`:** [RESEARCH_PROTOCOL.md — Filesystem structure](../RESEARCH_PROTOCOL.md#filesystem-structure).
