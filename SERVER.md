# Research Dashboard Web UI

A local web dashboard for monitoring and browsing research task execution, artifacts, and logs.

## Quick Start

```bash
# Install web dependencies (one-time)
.venv/bin/pip install -e ".[web]"

# Start the server
.venv/bin/python -m web

# Open browser
# http://127.0.0.1:5001
```

Optional flags:
```bash
.venv/bin/python -m web --port 5001 --host 127.0.0.1 --outputs /path/to/outputs
```

## Features

### Sidebar
- **Left panel** lists all research projects and their tasks
- Status badges:
  - 🟢 **Completed** — FINAL_RESPONSE.md exists
  - 🟡 **In Progress** — TASK_GRAPH.json has incomplete nodes (pulsing)
  - ⚪ **Planning** — No TASK_GRAPH.json yet
- Active (non-completed) tasks sort to the top
- Auto-refresh every 30 seconds

### Task Detail View
Click a task in the sidebar to load its detail panel with multiple tabs:

#### 1. Overview (default tab)
- **Research Request** — original prompt, deliverable constraints, approved search terms
- **Hyperparameters** — $InitialPromptVariants$, $WorkersPerTask$, $EarlyStoppingWorkers$, $MaxOrchestratorIterations$, etc.
- **Tasks** — checklist from TODO.md, organized by execution wave
- **Final Response** — link to view FINAL_RESPONSE.md if task is complete

#### 2. Timeline
- Chronological log of all execution events from `log_*.txt`
- Color-coded by role:
  - 🔵 **planning** — Stage I / director work
  - 🟢 **subtask** — orchestrator scope
  - 🟠 **worker** — delegated research run
  - 🟣 **validator** — grounding/verification run
  - ⚪ **step** — discrete actions (web searches, script calls, user decisions)
  - 🔵 **host_subagent** — CLI tool runs
- Shows duration (wall-clock seconds) for paired START/END blocks
- **Warning badges** appear for missing required fields (e.g., `delegation_type` on worker START blocks)
- **In-progress** indicator (pulsing yellow) for unpaired START blocks
- Status pills for completed events (success/failed/cancelled)

#### 3. Task Graph
- Directed acyclic graph of subtasks with dependencies
- Node status: completed (green) vs pending (gray)
- Dependency edges show prerequisite relationships
- **Expandable subtask accordions** — click to lazily load subtask details

#### 4. Subtask Details (loaded on demand from Task Graph tab)
- **Worker/Validator table** — parsed from `orchestrator_responses.md`, shows Copy | Worker | Validator pairs with clickable links to artifacts
- **Worker cards** — lists all workers for the subtask, shows model, copy, prompt_hash in metadata
- **Validator cards** — lists all validators, shows validation_status (passed/failed), control model, worker model
- **Related-work leads** — parsed table from `orchestrator_log.md` if present
- **Orchestrator log** — full narrative log rendered as markdown (collapsible)

#### 5. Artifact Viewer
Click any worker/validator file to open the artifact viewer:
- **YAML frontmatter** displayed as a table (role, model, copy, prompt_hash, validation_status, etc.)
- **Markdown body** rendered as HTML
- Includes `## Prompt`, `## Response`, `## Validator changelog`, `## Grounding notes` sections

## Parsing & Data Sources

All data parsed deterministically from existing files (no LLM parsing):

| File | Format | Parsed By |
|------|--------|-----------|
| `log_*.txt` | Blocks delimited by `--- {timestamp} {START\|END} {role} ---` | `log_parser.py` + reused `execution_log.py` regex |
| `TASK_GRAPH.json` | JSON DAG with nodes, edges, completed array | `task_graph.py` + reused `task_graph_waves.py` module |
| `worker-*.md` / `validator-*.md` | YAML frontmatter + markdown body | `frontmatter.py` + `markdown` library |
| `HYPERPARAMETERS.md` | Markdown table `\| Name \| Value \|` | `markdown_files.py` regex |
| `TODO.md` | Checkboxes `- [x] \`task-id\`` organized by ## Wave headers | `markdown_files.py` regex |
| `USER_PROMPT.md` | Sections: Original request, Deliverable constraints, Approved search terms | `markdown_files.py` regex |
| `orchestrator_responses.md` | Markdown table `\| Copy \| Worker \| Validator \|` | `markdown_files.py` regex (fallback to raw markdown on parse failure) |
| `orchestrator_log.md` | LLM-written narrative with `## Related-work leads` table | `markdown_files.py` regex for table (fallback to rendered markdown) |
| `FINAL_RESPONSE.md` | Free-form markdown | `markdown` library |

## Error Handling

- **Malformed data** — shows inline error boxes with traceback, never crashes
- **Missing files** — reported gracefully ("not found")
- **Parse failures** — fallback to raw markdown or show error + raw text
- **Path traversal** — blocked; artifact viewer validates paths stay within `outputs/`
- **Missing required fields** — warning badges on log events (e.g., `delegation_type`, `claims_challenged`)

## Auto-Refresh

- **Sidebar** — polls every 30 seconds for new projects/tasks
- **Active task tabs** — poll every 15 seconds if task status is `planning` or `in_progress`
- **Completed tasks** — no polling

## Architecture

**Tech stack:**
- Flask 3.0+ (Python web framework)
- Jinja2 (templates, built into Flask)
- htmx 2.0+ (AJAX, lazy-loading tabs)
- Pico CSS + custom CSS (classless styling, no build step)
- PyYAML (YAML frontmatter parsing)
- Python-Markdown (`.md` → HTML rendering)

**Modules:**
- `web/app.py` — Flask app factory, all routes
- `web/parsers/` — parsing logic for logs, graphs, frontmatter, markdown
- `web/templates/` — Jinja2 HTML templates (base + 6 partials)
- `web/static/` — CSS + minimal JS for tab switching

**Lazy loading:**
- Sidebar scans directory names only (no file reads)
- Task overview loads 3 small `.md` files on click
- Other tabs load on demand via htmx GET
- Subtask artifacts load on expand
- No caching layer needed (files are small, local I/O is fast)

## Development

Run tests:
```bash
.venv/bin/pytest web/
```

Logs are in `outputs/{project}/{task}/log_*.txt` for inspection/debugging.

## Known Limitations

- **Single-session server** — not deployed to production; use for local monitoring only
- **No real-time updates** — polling-based (not WebSocket); respects htmx trigger rules
- **Backward compatibility not enforced** — if log format changes, UI shows errors instead of trying to maintain compatibility
- **Orchestrator log parsing** — attempts to parse `## Related-work leads` table; falls back to rendered markdown if format changes
