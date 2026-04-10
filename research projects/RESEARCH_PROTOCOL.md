# Research protocol (agent-executable)

This document is the **canonical execution spec** for deep, grounded research managed by a research director (human) and executed by **coding agents** (CLI or IDE). **Quality and grounding take precedence over speed**; long runtimes are acceptable.

Notation: **`$X$`** names a hyperparameter; the prose after it explains its role. Agents copy concrete values into the active task folder (e.g. `TOOLS_AND_MCP.md` or a small `HYPERPARAMETERS.md`).

**Roles:** See [docs/ROLE_BINDING.md](docs/ROLE_BINDING.md) so workers and validators do not reinterpret themselves as orchestrators.

**Companion documents** (read alongside this protocol):

| Document | Purpose |
|----------|---------|
| [docs/SKILLS_AND_SCRIPTS.md](docs/SKILLS_AND_SCRIPTS.md) | **Canonical** curated skills table, `research_utils` index, TDD policy, how to add skills |
| [docs/ROLE_BINDING.md](docs/ROLE_BINDING.md) | **Invocation-scoped roles**, anti-loop rules, delegation preambles |
| [docs/HOST_TOOLS.md](docs/HOST_TOOLS.md) | Host context files, delegation, **pytest** / `PYTHONPATH` (commands are canonical here) |

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

- Contains this protocol, **shared docs** (`docs/`), **shared skills** (`skills/`), **shared scripts** (`scripts/`), and **templates** (`templates/`).

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
- **Execution log:** Maintain **one** append-only log per mission in **`outputs/{research-project-x}/{task-tldr}/`**. **Open** it using **`research_utils.execution_log.resolve_task_execution_log`**, which creates **`log_YYYY-MM-DD_HHMMSS.txt`** in **UTC** (same pattern as **`format_log_filename`**) when none exists, or continues the **latest** existing file that matches that pattern. **Append** each **START** / **END** line for **worker** and **validator** runs with **`render_execution_record`** and **`append_execution_record`**; without Python, serialize the same block shape those functions produce. **Each record carries:** task graph **id**, subtask folder name, child **prompt**, **artifact paths**, **status** (success / failed / cancelled; one-line **reason** if failed), **prompt hash**, **worker model**, **copy**, **`$ControlPlaneModel$`** on validators, optional host run id; keep full **response** text in the **`workers/`** / **`validators/`** files only. [Python helpers](#python-helpers).

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
6. Maintain a **TODO list** (e.g. `TODO.md`) mapping subtasks to future orchestrator folders, with **task ids** aligned to graph node ids. Persist the graph as **`TASK_GRAPH.json`** in **`outputs/{research-project-x}/{task-tldr}/`**. Run **`research_utils.task_graph_waves`** ([helper APIs](docs/SKILLS_AND_SCRIPTS.md#helper-apis-research_utils); skill [skills/research-task-graph-waves/SKILL.md](skills/research-task-graph-waves/SKILL.md)) to compute **execution waves** and an optional full **topological order**. After **new information** changes the plan, **update** `TASK_GRAPH.json`, pass the current **`completed`** node ids into the helper, **re-run** it so finished tasks are never rescheduled, then continue with the next wave or revised graph.
7. **Interview the user** until ambiguity is removed (scope, success criteria, forbidden sources, time/depth) — in addition to any term-level questions above.
8. **Deliverable length:** If the **original prompt** does **not** specify report length or depth, **ask** the user and record the answer under **`USER_PROMPT.md`** — **Deliverable constraints** (target words/pages or qualitative depth). A **protocol-default** depth (e.g. “use protocol default”) is valid **only** after the **user explicitly confirms** that default in follow-up messages — do **not** record such a waiver **unilaterally**. If length/depth **is** already in the **original prompt**, copy it under **Deliverable constraints** without re-asking. Stage III **`FINAL_RESPONSE.md`** must **honor** what is recorded (including any user-confirmed default).
9. **Identify tools, skills, MCP, and models**: consider what exists on the system, search for gaps, and **ask the user** if additional integrations are required. Follow [LLM / model IDs](#llm--model-ids) for discovery, confirmation, and recording **`$ControlPlaneModel$`** / **`$ModelsForThisTask$`** in `TOOLS_AND_MCP.md` or `MODELS.md`. Record other tool decisions in `TOOLS_AND_MCP.md`. **Confirm** MCP rows and model IDs with the user against the host; note limitations in `TOOLS_AND_MCP.md` and agree any fallback.
10. **Orchestrators (Stage II)** must read **`USER_PROMPT.md`**, take the **approved search terms**, and **weave them into every prompt variant** they generate (rephrase freely, but do not omit the vocabulary the Stage I pass validated unless the subtask text explicitly narrows scope). Subtask descriptions in `TODO.md` should remain consistent with those terms when they apply to the whole task.

### Stage II readiness gates

11. Do **not** start orchestrator delegation until **all** of the following hold. Only after planning is stable, create `{sub-task}` folders (when delegation applies) and proceed to Stage II. Task templates link here instead of restating this list.

    - **`USER_PROMPT.md`:** **Approved search terms (Stage I)** populated. **Deliverable constraints** include report length/depth **either** from the **original prompt** **or** from the user after you asked **or** a **user-confirmed** protocol-default (not agent-authored alone).
    - **`TOOLS_AND_MCP.md`:** **`$ControlPlaneModel$`** and **`$ModelsForThisTask$`** filled with **verbatim host model identifier strings** (no placeholders such as “session default”, “TBD”, or undocumented “same as session”). **User confirmation** of those IDs is **logged** here or under **`USER_PROMPT.md`** (verbatim quote or pasted approval).
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

**Skipping delegated Stage II** (single-session synthesis with **no** worker or validator children) is **never** allowed **unless** the **original user prompt** — the text under **Original request** in **`USER_PROMPT.md`** — **explicitly** asks for it (e.g. single-pass memo, no subagents, no delegated workers). **Do not** substitute mid-run “waivers”, agent-authored notes in **`USER_PROMPT.md`** or **`TOOLS_AND_MCP.md`**, or quoted user messages from **after** the mission started unless those messages **only** restate scope already present in the **original prompt**. When the original prompt **does not** request a skip, orchestrators **must** delegate workers and validators per [Orchestrator algorithm (per subtask)](#orchestrator-algorithm-per-subtask) and [ROLE_BINDING.md](docs/ROLE_BINDING.md).

### Orchestrator algorithm (per subtask)

1. From the **original** subtask prompt and task-level **`USER_PROMPT.md`**, generate variants that **incorporate** **Approved search terms** (synonyms ok; do **not** drop silently). Collect up to **`$InitialPromptVariants$`** uniques with **`research_utils.prompt_variants`** (dedupe keys; count every proposal—including duplicates—toward **`$MaxCountToFindUniquePrompts$`**; after each attempt call **`variant_collection_should_stop`** per [Helper APIs](docs/SKILLS_AND_SCRIPTS.md#helper-apis-research_utils)). When stop is true, proceed with uniques collected.
2. For **every** prompt variant, run **every** **worker** model in **`$ModelsForThisTask$`** with the **exact** same variant text (no silent narrowing).
3. For each **(prompt variant, worker model)** pair, run **`$WorkersPerTask$`** **delegated** workers, each labeled with **copy number**. Launch **worker** delegated runs **in parallel** across distinct slots when the host supports it. Each **worker** child must be launched with that slot’s **worker** model (from **`$ModelsForThisTask$`**).
4. For **each** worker slot, run the **validator** as a **delegated** session **immediately after** that worker finishes (**sequential** worker → validator **per** slot). Launch **every** validator child with **`$ControlPlaneModel$`** — **not** the worker’s model. **Before** the orchestrator accepts a worker result for consolidation, the corresponding validator output must exist: verify links and external sources where possible, **edit** the worker response so the orchestrator receives **grounded** text. If **no** grounded results remain after validation, the orchestrator **stops and asks the user** how to proceed.
5. The orchestrator **compares** validated outputs. If more effort is warranted and repeats are dominating, collect **additional unique** prompt variants by **re-running step 1** (do not restate variant-stop rules here). When **`$MaxOrchestratorIterations$`** is set, do not start more than that many **refinement rounds** after the initial worker wave (each round may add variants and fan out workers again).
6. If **no new information** is gained by further iterations, or the **`$MaxOrchestratorIterations$`** cap is reached when set, complete in-flight work and **stop** refining.
7. **Propagation:** If one worker surfaces **crucial** information **within the current subtask’s scope**, write it to `SHARED_CONTEXT.md` under this `{sub-task}` and ensure **new** workers include it. If that information **requires user disambiguation**, **ask the user first**, then propagate.
8. **Related-work leads and replan:** When validated worker output surfaces **substantive leads** from **related work** or equivalent sections (e.g. related papers, background, prior work, bibliography) that imply **new subgoals** **outside** the current subtask, record them in **`orchestrator_log.md`** and in **`SHARED_CONTEXT.md`** when they should inform **remaining work** in this subtask. **Ask the user** whether to run a **Stage I replan** (update `TODO.md`, **`TASK_GRAPH.json`**, and recompute waves). Do **not** silently omit such items. **Do not** add new **`TODO.md`** rows or **`TASK_GRAPH.json`** nodes from Stage II — that is **Stage I / director** work; who may edit what is summarized in [docs/ROLE_BINDING.md](docs/ROLE_BINDING.md).
9. **Basic flow:** orchestrator → worker → validator → orchestrator. Validators never skip straight to the user without notifying the orchestrator.

### Concurrency and delegation notes

- **Delegation shape:** As in [Orchestrator algorithm (per subtask)](#orchestrator-algorithm-per-subtask) steps 2–4 (workers on **`$ModelsForThisTask$`**, validators on **`$ControlPlaneModel$`**; parallel distinct worker slots when the host allows; sequential worker → validator per slot).
- **Broadcasting** to “running” workers means: update `SHARED_CONTEXT.md` and **start new delegated runs** (or re-prompt children) with the updated context. There is usually **no shared memory** between separate agent sessions.
- Log **intended** vs **completed** workers in `orchestrator_log.md` and optional `orchestrator_meta.json`. Task-level **`log_{datetime}.txt`** in **`outputs/{research-project-x}/{task-tldr}/`** ([Filesystem structure](#filesystem-structure)); prefer **`research_utils.execution_log`** ([Python helpers](#python-helpers)).

---

## Stage III — Final user response

After **all** orchestrators finish:

1. **Compile** one final answer for the user (executive summary, evidence map, open questions), respecting **Deliverable constraints** in **`USER_PROMPT.md`** (length/depth or agreed default). If **related-work** or **replan** escalations remain **pending** (e.g. user deferred Stage I updates), include them in **open questions**.
2. Write **`FINAL_RESPONSE.md`** in **`outputs/{research-project-x}/{task-tldr}/`**.
3. Ensure required artifacts exist with the fields described under **`workers/` and `validators/`** and **`{sub-task}`** in [Filesystem structure](#filesystem-structure) (orchestrator: subtask text, prompts, worker counts, prompt/response record).

---

## Auto-detection of skills, tools, and MCP

Any agent (orchestrator, worker, or validator) that notices behavior that would **generalize** across multiple research contexts must:

1. Draft an **evidence appendix**: at least **two** concrete instances from the current task, why a one-off fix is insufficient, and how reuse would work.
2. **Re-read** the evidence; if it is **not** general, **do not** ask the user — log a one-off note in `TODO.md` or the orchestrator log.
3. If still general, follow **[skills/research-skill-proposal/SKILL.md](skills/research-skill-proposal/SKILL.md)** and **ask the user** for approval before adding a skill, script, or MCP — include the evidence in the question.

---

## Python helpers

Deterministic logic lives in **`scripts/research_utils/`**. **Import path, venv, pytest, TDD:** [docs/HOST_TOOLS.md](docs/HOST_TOOLS.md#python) ([pyproject.toml](../pyproject.toml) for `pythonpath` / `testpaths`). **Module stub (names only):** [docs/SKILLS_AND_SCRIPTS.md#helper-apis-research_utils](docs/SKILLS_AND_SCRIPTS.md#helper-apis-research_utils). **When to call:** Stage I step 6 (`task_graph_waves`), Stage II step 1 (`prompt_variants` / `variant_collection_should_stop`), task-level log under **`outputs/{research-project-x}/{task-tldr}/`** ([Filesystem structure](#filesystem-structure)) via **`execution_log.resolve_task_execution_log`**, **`render_execution_record`**, **`append_execution_record`** (no pointer file).
