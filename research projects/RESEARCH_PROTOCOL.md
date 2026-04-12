# Research protocol (agent-executable)

This document is the **canonical execution spec** for deep, grounded research managed by a research director (human) and executed by **coding agents** (CLI or IDE). **Quality and grounding take precedence over speed**; long runtimes are acceptable.

Notation: **`$X$`** names a hyperparameter; the prose after it explains its role. Agents copy concrete values into the active task folder (e.g. `TOOLS_AND_MCP.md` or a small `HYPERPARAMETERS.md`).

**Roles:** See [docs/ROLE_BINDING.md](docs/ROLE_BINDING.md) so workers and validators do not reinterpret themselves as orchestrators.

**Companion documents** (read alongside this protocol):

| Document | Purpose |
|----------|---------|
| [docs/SKILLS_AND_SCRIPTS.md](docs/SKILLS_AND_SCRIPTS.md) | **Canonical** curated skills table, Python helper index, TDD policy, how to add skills |
| [docs/ROLE_BINDING.md](docs/ROLE_BINDING.md) | **Invocation-scoped roles**, anti-loop rules, delegation preambles |
| [docs/HOST_TOOLS.md](docs/HOST_TOOLS.md) | Host context files, delegation, **pytest** / `PYTHONPATH` (commands are canonical here) |
| [docs/DISCOVERED_SKILLS_FLOW.md](docs/DISCOVERED_SKILLS_FLOW.md) | `discovered-skills/` drafts; Stage II reflection; Stage III consolidation |

---

## Hyperparameters

| Name | Meaning |
|------|--------|
| `$InitialPromptVariants$` | Target count of **distinct** rephrasings of the orchestrator’s assigned prompt before the first worker wave. |
| `$MaxCountToFindUniquePrompts$` | Maximum **generation attempts** (each proposed variant counts once, including duplicates rejected by deduplication) while growing the unique set. When this cap is hit, proceed with all uniques collected so far (even if fewer than `$InitialPromptVariants$`). |
| `$WorkersPerTask$` | How many **delegated** worker runs to plan per **(prompt variant, worker model)** pair. Workers for a given wave should run **in parallel** when the host supports concurrent delegated sessions; log **intended** vs **completed** counts. |
| `$MaxOrchestratorIterations$` | Optional cap on **refinement rounds** after the initial worker wave (each round may add new unique prompt variants and fan out workers again), in addition to the “no new information” stop rule. |
| `$ControlPlaneModel$` | **Single** model identifier for the **orchestrator** session and **every validator** delegated run. The user confirms the exact string after host discovery; record it in `TOOLS_AND_MCP.md` or `MODELS.md`. Run the orchestrator on this model (host setting / session model). |
| `$ModelsForThisTask$` | **Worker pool only:** one or more model identifiers (after host discovery and user confirmation) used to **fan out workers** across models for coverage. You may omit **`$ControlPlaneModel$`** from this list unless you also want that model to run as a worker. Record exact strings in `TOOLS_AND_MCP.md` or `MODELS.md`. |

**Default robustness (readiness):** Unless the **original prompt** (the text under **Original request** in **`USER_PROMPT.md`**) **explicitly** narrows scope to a **single** worker model, a **single** copy per slot, or otherwise rules out multi-slot fan-out, satisfy **at least one** of: (i) **two or more** distinct entries in **`$ModelsForThisTask$`**, or (ii) **`$WorkersPerTask$` ≥ 2**. Rationale: multiple delegated slots reduce single-model blind spots.

---

## LLM / model IDs

**Discover** host identifiers, **confirm** **`$ControlPlaneModel$`** and **`$ModelsForThisTask$`** with the user, copy **exact strings** to `TOOLS_AND_MCP.md` or `MODELS.md` (roles: [Hyperparameters](#hyperparameters)). Mapping hosts to context files: [docs/HOST_TOOLS.md](docs/HOST_TOOLS.md). **Expectation:** workers on **`$ModelsForThisTask$`**, validators on **`$ControlPlaneModel$`**; if the host cannot mix models per child, record in `TOOLS_AND_MCP.md` and agree a fallback.

**Confirmation record:** After the user confirms model identifiers, log that confirmation in **`USER_PROMPT.md`** (e.g. **Model confirmation (Stage I)**) or **`TOOLS_AND_MCP.md`** with a short **verbatim** user quote or pasted approval. Placeholders such as “session default”, “Cursor default”, or “TBD” **do not** satisfy [Stage II readiness gates](#stage-ii-readiness-gates).

---

## Filesystem structure

Paths below are relative to the **repository root** unless stated otherwise.

### Framework (`research projects/`)

- Contains this protocol, **shared docs** (`docs/`), and **templates** (`templates/`). **Shared skills** live in **`.agents/skills/`** at the repo root (including optional **`skills/<name>/scripts/`** Python per skill).

### Task outputs (`outputs/`)

- **All** mission artifacts (Stage I–III files, subtask folders, logs) live under **`outputs/`** at the repository root, e.g. `outputs/{research-project-x}/{task-tldr}/` and `outputs/{research-project-x}/{task-tldr}/{sub-task}/`.
- Typical project slug example: `outputs/recursive-llm-self-improvement/<task-tldr>/` for work under that research program.

**`outputs/{research-project-x}/`** — one folder per broad research program.

- Entry point for all questions that belong to the same overall topic.
- Agents **may** read final reports from **earlier tasks under this same project** (same `{research-project-x}` under `outputs/`).
- Agents **must not** reference data from **other** `{research-project-x}` directories under `outputs/`.

**`outputs/{research-project-x}/{task-tldr}/`** — one folder per distinct user query / mission.

- **Save:** the user’s prompt, **Stage I approved search terms** (same artifact as the prompt — see [Stage I](#stage-i--initial-planning)), the generated TODO list, **`TASK_GRAPH.json`** (directed acyclic subgoal graph and optional `completed` ids), the final consolidated response.
- **Save:** `TOOLS_AND_MCP.md` (and optionally `MODELS.md`) listing skills, tools, MCP servers, and models relevant to **this** task.
- **`discovered-skills/`** (optional): draft **proposals only** for reusable skills/scripts/MCP ideas from Stage II — **not** canonical shared skills (those live in `.agents/skills/`). Normative flow: [docs/DISCOVERED_SKILLS_FLOW.md](docs/DISCOVERED_SKILLS_FLOW.md).
- **Execution log:** One append-only canonical **`log_*.txt`** (UTC) in this folder; use **`execution_log`** ([Helper APIs](docs/SKILLS_AND_SCRIPTS.md#helper-apis)) for open/append. Every phase below uses **START** then **END** (same UTC block header shape); **never** log only **END** for a paired run.
  - **`planning`:** Stage I / director work in **`{task-tldr}/`** (initial or replan). **Fields:** `planning_phase` (`stage1_initial` | `stage1_replan`), optional `trigger`; **END** may include `todo_rows`, `task_graph_nodes`, `waves_computed` (`yes` / `no`).
  - **`subtask`:** Orchestrator scope for one **`{sub-task}/`**. **START** before the first worker delegation for that folder; **END** when the subtask is complete. **Fields:** task graph **id**, **subtask** folder name, optional `wave` / notes; **END** includes **status** (success / failed / cancelled; one-line **reason** if failed).
  - **`worker`** / **`validator`:** Each delegated child. **Fields:** task graph **id**, subtask folder name, child **prompt**, **artifact paths**, **status** on **END** (success / failed / cancelled; one-line **reason** if failed), **prompt hash**, **worker model**, **copy**, **`$ControlPlaneModel$`** on validators, optional host run id; full **response** text stays in **`workers/`** / **`validators/`** only. **`delegation_type`** (**required** on START): how the child was launched — `host_subagent` | `background_agent` | `inline_single_session` | other host-specific string. Validator **END** blocks should include **`claims_challenged`** (count of claims edited or removed) and **`links_checked`** (count of URLs verified) when available.
  - **`host_subagent`:** When the orchestrator (or director, if applicable) uses a **host Task** or equivalent **other than** worker/validator children (e.g. explore, shell). **START** before launch, **END** after return. **Fields:** **`subagent_type`** (e.g. `explore`, `shell`, `generalPurpose`, `best-of-n-runner`), short **`purpose`**, optional task graph **id** / **subtask** folder.
  - **`step`:** Point-in-time event **within** another phase — does **not** require a START/END pair (single START block only). Use `log_step` from `execution_log` or emit the block shape manually. **Fields:** **`parent_role`** (the enclosing role, e.g. `planning`, `subtask`), **`action`** (see actions below), plus action-specific fields. **Actions:**
    - `script_call` — a Python helper was invoked. Fields: `script` (e.g. `task_graph_waves.execution_waves`), optional `result` summary.
    - `skill_invocation` — a skill SKILL.md was opened. Fields: `skill` (e.g. `research-worker`), optional `invoked_by`.
    - `prompt_variant_collection` — dedup stats after prompt generation. Fields: `candidates_generated`, `unique_accepted`, `duplicates_rejected`, `stop_reason` (`target_reached` | `max_attempts_exhausted`).
    - `user_decision` — the process branched on user input. Fields: `question` (what was asked), `decision` (approved / rejected / deferred), optional `notes`.
    - `web_search` — a search was performed during planning. Fields: `query`, optional `results_summary`.
    - `related_work_lead` — the orchestrator identified a substantive lead from validated worker output that may imply new subgoals outside the current subtask. Fields: `lead_summary` (one-line description), `source_artifacts` (list of worker/validator files that surfaced it), `implies_new_subgoal` (`yes` | `no`), `escalated_to_user` (`yes` | `no` | `pending`), optional `dedup_note` (e.g. "corroborates lead X from worker-..., not re-escalating").
  - **`duration_s`:** Any **END** block **should** include a `duration_s` field (wall-clock seconds since the matching START). Prefer **`log_end_event`** (computes `duration_s` and generates the timestamp automatically) or use `parse_duration_from_start` from `execution_log`.
  - Without Python, match the block shape those helpers produce.

**`outputs/{research-project-x}/{task-tldr}/{sub-task}/`** — one folder per **orchestrator** line item from the TODO.

- Orchestrator artifacts: subtask description, generated prompts, worker counts (initiated / finished successfully), plus a file of prompt/response pairs for consolidation. See **Stage III** and templates.

**`workers/` and `validators/`** under each `{sub-task}` directory:

- Worker: prompt, **worker** model slug, copy number, response.
- Validator: same prompt/copy/prompt hash as the worker file; **worker** model slug in the filename (for pairing); validated response. Front matter records **`worker_model`** (the draft’s model) and **`control_model`** (**`$ControlPlaneModel$`** that performed validation). Validator **edits** the worker output; it does not replace research with new synthesis.

Suggested filenames (hash = short stable id, e.g. first 8 chars of SHA-256 of normalized prompt; `{model-slug}` = **worker** model):

- `workers/worker-{model-slug}-{copy}-{promptHash}.md`
- `validators/validator-{model-slug}-{copy}-{promptHash}.md`

---

## Stage I — Initial planning

Stage I **starts** with **search-oriented term discovery** on the user’s prompt, then continues with decomposition and tooling. Do **not** classify a candidate term’s relatedness from intuition alone — use **web search** (and, if available, comparable host tools) so each keep/drop/ask decision is **grounded in what retrieval actually returns** for that term in context of the mission.

### Search terms (first)

1. **Extract entities and candidate phrases** from the original prompt (named entities, technical jargon, product names, acronyms, alternate phrasings that might appear in sources).
2. For **each** candidate term, run **at least one targeted web search** (query may combine the term with words from the prompt). From the **results** (titles, snippets, top pages — not model guesses), decide:
   - **Very related** to the prompt’s topic → **approve** and **track** the term.
   - **Clearly unrelated** (results show a different sense, wrong domain, or no substantive link) → **drop**; do **not** add to the approved list.
   - **Medium / ambiguous** (results are mixed or the link to the mission is unclear) → **ask the user** whether to include the term; if the user approves, add it to the approved list (note the decision under **Clarifications** in `USER_PROMPT.md`).
3. **Persist approved terms** in **`USER_PROMPT.md`** in the section **Approved search terms (Stage I)**, with a **short basis** per term (e.g. query used + one-line takeaway from what you read). This file is the **single task-level source of truth** for terms that Stage II must use.
4. Only after this pass (and any user follow-up for ambiguous terms), continue with [Survey and review literature (when applicable)](#survey-and-review-literature-when-applicable), then the steps under **Planning and handoff** below.

### Survey and review literature (when applicable)

For **academic** or **survey-heavy** missions, treat survey and review papers as **first-class** planning inputs **before** you author **`TASK_GRAPH.json`** (and thus before **topological order** / execution waves are fixed).

- **Prioritize** targeted **web search** for **survey papers**, **review articles**, **systematic reviews**, or field-standard overview material (combine approved or domain terms with patterns such as `survey`, `review`, `tutorial overview`, `state of the art`).
- **Parse** what you can from titles, abstracts, and accessible sections: **vocabulary**, **taxonomy / decomposition of the research space**, **open problems**, and **canonical references**.
- **Fold** that structure into **decomposition** (step 5 below) and, where useful, add terms to **Approved search terms (Stage I)** with a **short basis**—all **before** locking **`TASK_GRAPH.json`**.
- If it is **unclear** whether surveys are relevant to the mission or which subfield’s surveys to trust, **ask the user** before locking the graph.

### Planning and handoff

5. **Plan** before heavy execution: decompose the user’s goal into **subtasks** at a granularity similar to high-level task decomposition in coding agents. Represent the decomposition as a **directed acyclic graph**: **nodes** are tasks (stable **id** + short **description**); **edges** encode precedence (`A → B` means **A finishes before B starts**). A **linear chain** is valid; **parallel branches** are allowed when the mission truly has independent or alternative workstreams—avoid unnecessary complexity. Do **not** rely on informal ordering alone for execution scheduling.
6. Maintain **TODO.md** (or equivalent) with **task ids** aligned to the graph. Write **`TASK_GRAPH.json`** in **`outputs/{research-project-x}/{task-tldr}/`**. Run **`task_graph_waves`** per [research-task-graph-waves/SKILL.md](../.agents/skills/research-task-graph-waves/SKILL.md) for **waves** (and optional topo order). On replan, update **`completed`** and re-run so finished tasks are never rescheduled.
7. **Interview the user** until ambiguity is removed (scope, success criteria, forbidden sources, time/depth) — in addition to any term-level questions above.
8. **Deliverable length:** If the **original prompt** does **not** specify report length or depth, **ask** the user and record the answer under **`USER_PROMPT.md`** — **Deliverable constraints** (target words/pages or qualitative depth). A **protocol-default** depth (e.g. “use protocol default”) is valid **only** after the **user explicitly confirms** that default in follow-up messages — do **not** record such a waiver **unilaterally**. If length/depth **is** already in the **original prompt**, copy it under **Deliverable constraints** without re-asking. Stage III **`FINAL_RESPONSE.md`** must **honor** what is recorded (including any user-confirmed default).
9. **Identify tools, skills, MCP, and models**: consider what exists on the system, search for gaps, and **ask the user** if additional integrations are required. Follow [LLM / model IDs](#llm--model-ids) for discovery, confirmation, and recording **`$ControlPlaneModel$`** / **`$ModelsForThisTask$`** in `TOOLS_AND_MCP.md` or `MODELS.md`. Record other tool decisions in `TOOLS_AND_MCP.md`. **Confirm** MCP rows and model IDs with the user against the host; note limitations in `TOOLS_AND_MCP.md` and agree any fallback.
10. **Orchestrators (Stage II)** must read **`USER_PROMPT.md`**, take the **approved search terms**, and **weave them into every prompt variant** they generate (rephrase freely, but do not omit the vocabulary the Stage I pass validated unless the subtask text explicitly narrows scope). Subtask descriptions in `TODO.md` should remain consistent with those terms when they apply to the whole task.

### Stage II readiness gates

11. Do **not** start orchestrator delegation until **all** of the following hold. Only after planning is stable, create `{sub-task}` folders (when delegation applies) and proceed to Stage II. Task templates link here instead of restating this list.

    - **`USER_PROMPT.md`:** **Approved search terms (Stage I)** populated. **Deliverable constraints** include report length/depth **either** from the **original prompt** **or** from the user after you asked **or** a **user-confirmed** protocol-default (not agent-authored alone).
    - **`TOOLS_AND_MCP.md`:** **`$ControlPlaneModel$`** and **`$ModelsForThisTask$`** filled with **verbatim** host model identifier strings and **logged user confirmation** per [LLM / model IDs](#llm--model-ids) (no placeholders such as “session default”, “TBD”, or “same as session”).
    - **Default robustness:** [Hyperparameters — Default robustness](#hyperparameters) satisfied unless the **original prompt** explicitly narrows fan-out.
    - **MCP / tools:** Listed for the mission, or gaps documented **with user approval**.
    - **Delegation vs. folders:** If the **original prompt** does **not** [explicitly permit skipping delegated Stage II](#delegation-requirement), create **`{sub-task}/`** folders per **`TODO.md`** orchestrator rows before running Stage II, and do **not** treat **`FINAL_RESPONSE.md`** as a substitute for the **`workers/`** / **`validators/`** artifact tree.

---

## Stage II — Subtask execution (orchestrator, worker, validator)

**Delegation permissions, anti-loop rules, and preambles** (use when spawning children): [docs/ROLE_BINDING.md](docs/ROLE_BINDING.md).

- **Orchestrator** — **one** `{sub-task}/` on **`$ControlPlaneModel$`**; runs the algorithm below (prompt variants, delegated workers and validators, consolidation).
- **Worker** — **one** slot: (prompt variant, model from **`$ModelsForThisTask$`**, copy index).
- **Validator** — **one** worker artifact on **`$ControlPlaneModel$`**; returns an **edited**, grounded worker response (or structured failure) to the orchestrator.

### Delegation requirement

**Skipping delegated Stage II** (single-session synthesis with **no** worker or validator children) is governed by three rules:

- **Default — must delegate.** Orchestrators **must** delegate workers and validators per [Orchestrator algorithm (per subtask)](#orchestrator-algorithm-per-subtask) and [ROLE_BINDING.md](docs/ROLE_BINDING.md).
- **Only exception.** The **original user prompt** — the text under **Original request** in **`USER_PROMPT.md`** — **explicitly** asks for a single-pass memo, no subagents, or no delegated workers.
- **No mid-run waivers.** Agent-authored notes in **`USER_PROMPT.md`** / **`TOOLS_AND_MCP.md`**, and quoted user messages from **after** the mission started, do **not** count — unless those messages only restate scope already present in the original prompt.

### Orchestrator algorithm (per subtask)

1. From the **original** subtask prompt and **`USER_PROMPT.md`**, generate variants that **incorporate** **Approved search terms** (synonyms ok; do **not** drop silently). Collect up to **`$InitialPromptVariants$`** uniques; each attempt counts toward **`$MaxCountToFindUniquePrompts$`** (including rejected duplicates). When the budget is hit, proceed with uniques collected so far. Use **`prompt_variants`** helpers for deduplication and stop logic ([Helper APIs](docs/SKILLS_AND_SCRIPTS.md#helper-apis)).
2. For **every** prompt variant, run **every** **worker** model in **`$ModelsForThisTask$`** with the **exact** same variant text (no silent narrowing).
3. For each **(prompt variant, worker model)** pair, run **`$WorkersPerTask$`** **delegated** workers, each labeled with **copy number**. Launch **worker** delegated runs **in parallel** across distinct slots when the host supports it. Each **worker** child must be launched with that slot’s **worker** model (from **`$ModelsForThisTask$`**).
4. For **each** worker slot, run the **validator** as a **delegated** session **immediately after** that worker finishes (**sequential** worker → validator **per** slot). Launch **every** validator child with **`$ControlPlaneModel$`** — **not** the worker’s model. **Before** the orchestrator accepts a worker result for consolidation, the corresponding validator output must exist: verify links and external sources where possible, **edit** the worker response so the orchestrator receives **grounded** text. If **no** grounded results remain after validation, the orchestrator **stops and asks the user** how to proceed.
5. The orchestrator **compares** validated outputs. If more effort is warranted and repeats are dominating, collect **additional unique** prompt variants by **re-running step 1** (do not restate variant-stop rules here). When **`$MaxOrchestratorIterations$`** is set, do not start more than that many **refinement rounds** after the initial worker wave (each round may add variants and fan out workers again).
6. If **no new information** is gained by further iterations, or the **`$MaxOrchestratorIterations$`** cap is reached when set, complete in-flight work and **stop** refining.
7. **Propagation:** If one worker surfaces **crucial** information **within the current subtask’s scope**, write it to `SHARED_CONTEXT.md` under this `{sub-task}` and ensure **new** workers include it. If that information **requires user disambiguation**, **ask the user first**, then propagate.
8. **Related-work leads and replan:** After each wave of workers/validators, scan validated output for **substantive leads** from **related work** or equivalent sections (e.g. related papers, background, prior work, bibliography) that imply **new subgoals** **outside** the current subtask. For each lead, **dedup** against the `## Related-work leads` section in **`orchestrator_log.md`** — if a substantially similar lead already exists, note it as corroborating evidence rather than creating a duplicate. Record **net-new** leads in that section and log a **`related_work_lead`** step event per lead (see [Execution log](#filesystem-structure)). Mirror to **`SHARED_CONTEXT.md`** only when leads inform **remaining work** in this subtask. After the wave completes, **batch-escalate** all net-new leads that imply new subgoals and **ask the user once** whether to run a **Stage I replan** (update `TODO.md`, **`TASK_GRAPH.json`**, and recompute waves); log a **`user_decision`** step referencing the leads. Do **not** re-escalate leads the user has already seen. Do **not** silently omit leads. **Do not** add new **`TODO.md`** rows or **`TASK_GRAPH.json`** nodes from Stage II — that is **Stage I / director** work; who may edit what is summarized in [docs/ROLE_BINDING.md](docs/ROLE_BINDING.md).
9. **Basic flow:** orchestrator → worker → validator → orchestrator. Validators never skip straight to the user without notifying the orchestrator.

### Concurrency and delegation notes

- **Delegation shape:** As in [Orchestrator algorithm (per subtask)](#orchestrator-algorithm-per-subtask) steps 2–4 (workers on **`$ModelsForThisTask$`**, validators on **`$ControlPlaneModel$`**; parallel distinct worker slots when the host allows; sequential worker → validator per slot).
- **Broadcasting** to “running” workers means: update `SHARED_CONTEXT.md` and **start new delegated runs** (or re-prompt children) with the updated context. There is usually **no shared memory** between separate agent sessions.
- Log **intended** vs **completed** workers in `orchestrator_log.md` (and optional `orchestrator_meta.json`). Task-level event logging — canonical filename, helper, and START/END field contract — lives in [Filesystem structure → Execution log](#filesystem-structure).

---

## Stage III — Final user response

After **all** orchestrators finish:

1. **Compile** one final answer for the user (executive summary, evidence map, open questions), respecting **Deliverable constraints** in **`USER_PROMPT.md`** (length/depth or agreed default). If **related-work** or **replan** escalations remain **pending** (e.g. user deferred Stage I updates), include them in **open questions**.
2. Write **`FINAL_RESPONSE.md`** in **`outputs/{research-project-x}/{task-tldr}/`**.
3. Ensure required artifacts exist with the fields described under **`workers/` and `validators/`** and **`{sub-task}`** in [Filesystem structure](#filesystem-structure) (orchestrator: subtask text, prompts, worker counts, prompt/response record).
4. **[Discovered-skills consolidation](docs/DISCOVERED_SKILLS_FLOW.md#stage-iii-consolidation):** Run it or record **N/A** (no `proposed-*.md`). Default: after step 2.

---

## Reusable skills, tools, and MCP

[docs/DISCOVERED_SKILLS_FLOW.md](docs/DISCOVERED_SKILLS_FLOW.md) — Stage II reflection, Stage III consolidation, **research-skill-proposal** for implementation; optional direct **research-skill-proposal** when the user explicitly requests an out-of-band shared change.
