# AGENTS.md — index

This repo supports **deep, grounded research** workflows for **any coding agent** (terminal CLI or IDE): humans and agents follow a shared protocol, write artifacts under `research projects/`, use project-local **skills** (`research projects/skills/`), and **stay within** the current `research projects/{research-project-x}/` tree (do not cite artifacts from sibling project folders). Isolation and layout: [research projects/RESEARCH_PROTOCOL.md](research%20projects/RESEARCH_PROTOCOL.md#filesystem-structure).

## Read next

| Document | Purpose |
|----------|---------|
| [research projects/RESEARCH_PROTOCOL.md](research%20projects/RESEARCH_PROTOCOL.md) | Canonical Stages I–III, layout, hyperparameters |
| [research projects/docs/SKILLS_AND_SCRIPTS.md](research%20projects/docs/SKILLS_AND_SCRIPTS.md) | **Canonical** curated skills table, `research_utils` index, TDD policy, how to add skills |
| [research projects/docs/ROLE_BINDING.md](research%20projects/docs/ROLE_BINDING.md) | **Invocation-scoped roles**, anti-loop rules, delegation preambles |
| [research projects/docs/HOST_TOOLS.md](research%20projects/docs/HOST_TOOLS.md) | Host context files, delegation, **pytest** / `PYTHONPATH` (commands are canonical here) |

## Python tests

Helpers live under `research projects/scripts/research_utils/`; commands, `PYTHONPATH`, venv, pytest, and TDD for `scripts/`: [research projects/docs/HOST_TOOLS.md](research%20projects/docs/HOST_TOOLS.md#python).
