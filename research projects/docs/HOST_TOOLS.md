# Host tools and context files

This repository is **host-agnostic**: no required `.cursor/` or `.claude/` directory. Use the table below to map the protocol to your environment.

| Host | Typical context files | Delegation mechanism | Documentation |
|------|------------------------|----------------------|---------------|
| **Gemini CLI** | `GEMINI.md` (default); can add `AGENTS.md` via `context.fileName` | Subagents, parallel sessions, or sequential runs | [Project context (GEMINI.md)](https://geminicli.com/docs/cli/gemini-md/), [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) |
| **Claude Code** | `CLAUDE.md`, often `AGENTS.md` | Subagents in `.claude/agents/` or `--agents` JSON | [Subagents](https://code.claude.com/docs/en/sub-agents) |
| **Cursor (example IDE)** | `AGENTS.md`, editor settings | Agent mode, Task/subagent flows, [background agents](https://docs.cursor.com/background-agents) | [docs.cursor.com](https://docs.cursor.com/) |
| **Other agents** | `AGENTS.md` ([agents.md](https://agents.md) ecosystem) | Your product’s subprocess or tool delegation | Vendor docs |

**Models:** Paste user-confirmed IDs into the active task’s `TOOLS_AND_MCP.md` / `MODELS.md` as **exact host strings**. Discovery, roles, and confirmation workflow: [LLM / model IDs](../RESEARCH_PROTOCOL.md#llm--model-ids) (see [Hyperparameters](../RESEARCH_PROTOCOL.md#hyperparameters)).

## Python

**Canonical commands** (repository root; virtual environment optional):

```bash
python3.11 -m venv .venv && .venv/bin/pip install pytest && .venv/bin/python -m pytest
```

`pythonpath` and `testpaths` are set in [pyproject.toml](../../pyproject.toml). To import helpers in a one-off script:

```bash
PYTHONPATH="research projects/scripts" python -c "from research_utils.prompt_variants import try_add_unique; ..."
```

**TDD:** New or changed behavior under `research projects/scripts/` needs **pytest** coverage — requirement and rationale: [SKILLS_AND_SCRIPTS.md § Tests and TDD](SKILLS_AND_SCRIPTS.md#tests-and-tdd).

## No in-repo LLM API

Orchestration does **not** call cloud LLM APIs from this repo’s Python code; agents use their **host** for inference and tools.
