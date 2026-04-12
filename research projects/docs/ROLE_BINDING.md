# Role binding (invocation-scoped)

## Principle

**Your effective role is set by the current invocation** (explicit instruction from the user or parent agent), not by browsing the repo. [AGENTS.md](../../AGENTS.md) is an index only—not every session is an orchestrator. That avoids **orchestrator → worker → “I am an orchestrator” → more workers** loops.

Which `SKILL.md` to open for each role: [Fundamental skills (default workflow)](SKILLS_AND_SCRIPTS.md#fundamental-skills-default-workflow). This document covers **role binding** and **delegation preambles** only.

## Roles at a glance

| | Orchestrator | Worker | Validator |
|---|--------------|--------|-----------|
| **Scope** | One `{sub-task}/` folder (`$ControlPlaneModel$`) | Single (prompt, **worker** model, copy) | One worker artifact (validator runs on `$ControlPlaneModel$`) |
| **Primary skill** | [^skill] | [^skill] | [^skill] |
| **May delegate** workers/validators | Yes | **No** | **No** |
| **May run Stage I / edit `TODO.md` for new subtasks** | **No** (that is Stage I / director) | **No** | **No** |
| **May open orchestrator skill** | Yes | **Only if user explicitly reassigned you** | **No** |

[^skill]: Open [Fundamental skills (default workflow)](SKILLS_AND_SCRIPTS.md#fundamental-skills-default-workflow) and use the row for Stage I planning, orchestrator, worker, or validator as appropriate.

## Anti-loop rules

The `FORBIDDEN:` blocks in the [delegation preambles](#delegation-preambles-copy-from-orchestrator-or-human) below are the enforced constraints for each role. In summary: workers must not delegate or orchestrate; validators must not perform new research or delegate. If generic repo context conflicts with the preamble a session received, **the preamble wins**.

## Delegation preambles (copy from orchestrator or human)

Prepend one of these blocks **verbatim** (fill placeholders) when starting a **child** agent run.

### `DELEGATION_PREAMBLE_WORKER`

```text
ROLE: WORKER (not orchestrator, not Stage I planning).
FORBIDDEN: Spawning workers or validators; editing TODO.md for new subtasks; opening research-orchestrator/SKILL.md; creating new {sub-task} folders.
REQUIRED: Follow research-worker/SKILL.md only. Write output to the path given below.
SUB-TASK DIR: <path>
TASK_ROOT: <absolute or repo-relative path to outputs/.../{task-tldr}/>
OUTPUT FILE: <path>
PROMPT (verbatim): <...>
WORKER MODEL (host — run this child with this model): <slug from $ModelsForThisTask$>
COPY INDEX: <n>
```

<a id="delegation-preamble-validator"></a>

### `DELEGATION_PREAMBLE_VALIDATOR`

```text
ROLE: VALIDATOR (not orchestrator, not worker research).
FORBIDDEN: Open-ended new research; spawning workers; orchestration.
REQUIRED: Follow research-validator/SKILL.md only. Edit/ground the given worker file; write validator output to the path below.
TASK_ROOT: <absolute or repo-relative path to outputs/.../{task-tldr}/>
VERIFICATION_STANCE:
- Intent: find faults in the worker draft (unsupported claims, citation–claim mismatch, overgeneralization, missing evidence)—not to rubber-stamp or polish by default.
- Skeptical default: treat claims as unproven until sources or checks support them; do not give the benefit of the doubt to paraphrases or URLs.
- Fault-finding applies only by editing/grounding this artifact; FORBIDDEN above still applies (no open-ended research, no delegation).
HOST: Start this delegated session with CONTROL MODEL only (same as orchestrator).
CONTROL MODEL (exact host ID): <$ControlPlaneModel$>
WORKER FILE: <path>
OUTPUT FILE: <path>
```

## Optional host patterns

Host-specific delegation and context-file patterns: [HOST_TOOLS.md](HOST_TOOLS.md).
