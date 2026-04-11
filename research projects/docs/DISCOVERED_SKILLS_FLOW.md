# Discovered skills flow

Task-local drafts under **`outputs/.../{task-tldr}/discovered-skills/`**; shared skills only after Stage III approval → [research-skill-proposal/SKILL.md](../skills/research-skill-proposal/SKILL.md). Full normative context: [RESEARCH_PROTOCOL.md](../RESEARCH_PROTOCOL.md).

## Paths and files

- **Location:** `discovered-skills/` at **task root** (sibling of `{sub-task}/`), not inside each subtask. From a subtask: **`../discovered-skills/`** or **`{TASK_ROOT}/discovered-skills/`** ([ROLE_BINDING.md](ROLE_BINDING.md) preambles).
- **Create folder:** Prefer at Stage I (optional [templates/discovered-skills/README.md](../templates/discovered-skills/README.md)); else first proposal creates it.
- **Draft shape:** Full future-`SKILL.md` draft (YAML `name`, `description`, body: **Trigger**, **Steps**, **Boundaries**, **Evidence from this run**) + **`Change type`** when relevant (`new skill` | `new script` | `new MCP` | `extend existing`).
- **Filename:** `proposed-{role}-{subtaskFolder}-{short-slug}.md` (ASCII).

<a id="stage-ii-reflection"></a>

## Stage II — reflection (orchestrator, worker, validator)

**Same process for every Stage II role** after that role’s **primary artifact** for the invocation (or when abandoning a line of work with clear lessons):

1. Would a **set of actions** help in **different** research contexts? If **no**, stop.
2. If **yes**, write **one** new file under `discovered-skills/` (naming above).
3. **Second pass:** Re-read it. If not confident it is reusable, **delete** the file (no stub).

**Rules:** No user approval requests in Stage II for routine discovery. Do **not** write under `research projects/skills/` until post–Stage III approval.

<a id="stage-iii-consolidation"></a>

## Stage III — consolidation

Director session; [RESEARCH_PROTOCOL — Stage III](../RESEARCH_PROTOCOL.md#stage-iii--final-user-response). **Default:** run **after** `FINAL_RESPONSE.md` (or document if you run earlier).

1. List `discovered-skills/proposed-*.md` (skip `_superseded/`, `rejected/` if used).
2. Drop or reject files that are not multi-context reusable.
3. Cluster similar drafts; **merge** each cluster to one file (`merged-{slug}.md`); move merged sources to `_superseded/` or delete. Singletons can stay.
4. For each candidate: user **approve** or **reject** (one-by-one); log in **`APPROVAL_LOG.md`**. Approved → **research-skill-proposal** (implement + tests + optional Fundamental row in [SKILLS_AND_SCRIPTS.md](SKILLS_AND_SCRIPTS.md)).

**Edge cases:** Empty after filter → no approval prompts; note **N/A**. User can still request **research-skill-proposal** directly for urgent out-of-band adds.

**Non-goals:** No required clustering code; no `.cursor`/host store changes.
