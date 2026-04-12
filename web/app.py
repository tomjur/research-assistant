"""Flask app factory for the research dashboard."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Add .agents/skills/*/scripts to sys.path (same pattern as conftest.py)
_ROOT = Path(__file__).resolve().parent.parent
for _scripts in sorted((_ROOT / ".agents" / "skills").glob("*/scripts")):
    if _scripts.is_dir():
        _s = str(_scripts)
        if _s not in sys.path:
            sys.path.insert(0, _s)

from flask import Flask, render_template, request, abort

from .parsers.project_scanner import list_projects, list_tasks, task_dir_for
from .parsers.log_parser import parse_log_file, pair_events, find_log_file
from .parsers.task_graph import load_task_graph_with_waves
from .parsers.frontmatter import parse_frontmatter, scan_subtask_artifacts
from .parsers.markdown_files import (
    load_markdown_rendered,
    parse_hyperparameters,
    parse_todo_items,
    parse_user_prompt_sections,
    parse_orchestrator_responses_table,
    parse_orchestrator_log_leads,
)


def create_app(outputs_dir: str | None = None) -> Flask:
    if outputs_dir is None:
        outputs_path = _ROOT / "outputs"
    else:
        outputs_path = Path(outputs_dir).resolve()

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    app.config["OUTPUTS_DIR"] = outputs_path

    def _safe(fn, *args, **kwargs):
        """Call fn, return (result, None) or (None, error_str) on failure."""
        try:
            return fn(*args, **kwargs), None
        except Exception:
            return None, traceback.format_exc()

    def _task_path(project: str, task: str) -> Path:
        td = task_dir_for(outputs_path, project, task)
        if td is None:
            abort(404)
        resolved = td.resolve()
        if not resolved.is_relative_to(outputs_path.resolve()):
            abort(403)
        return td

    # ── Index ──────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        projects, err = _safe(list_projects, outputs_path)
        return render_template("base.html", projects=projects, error=err)

    # ── Sidebar partials ──────────────────────────────────────────────
    @app.route("/api/projects")
    def api_projects():
        projects, err = _safe(list_projects, outputs_path)
        if err:
            return render_template("partials/error.html", error=err)
        return render_template("sidebar.html", projects=projects)

    @app.route("/api/projects/<project>/tasks")
    def api_project_tasks(project: str):
        tasks, err = _safe(list_tasks, outputs_path / project)
        if err:
            return render_template("partials/error.html", error=err)
        return render_template("sidebar.html", projects=[{"name": project, "tasks": tasks}])

    # ── Task detail (lazy container with sub-tabs) ────────────────────
    @app.route("/api/task/<project>/<task>")
    def api_task_detail(project: str, task: str):
        td = _task_path(project, task)
        tasks, _ = _safe(list_tasks, outputs_path / project)
        status = "unknown"
        if tasks:
            for t in tasks:
                if t["tldr"] == task:
                    status = t["status"]
                    break
        return render_template(
            "task_detail.html", project=project, task=task, status=status
        )

    # ── Overview tab ──────────────────────────────────────────────────
    @app.route("/api/task/<project>/<task>/overview")
    def api_overview(project: str, task: str):
        td = _task_path(project, task)
        hp, hp_err = _safe(parse_hyperparameters, td / "HYPERPARAMETERS.md")
        todo, todo_err = _safe(parse_todo_items, td / "TODO.md")
        prompt, prompt_err = _safe(parse_user_prompt_sections, td / "USER_PROMPT.md")
        final_exists = (td / "FINAL_RESPONSE.md").exists()
        return render_template(
            "partials/overview.html",
            hyperparams=hp, hp_err=hp_err,
            todo=todo, todo_err=todo_err,
            prompt=prompt, prompt_err=prompt_err,
            final_exists=final_exists,
            project=project, task=task,
        )

    # ── Timeline tab ──────────────────────────────────────────────────
    @app.route("/api/task/<project>/<task>/timeline")
    def api_timeline(project: str, task: str):
        td = _task_path(project, task)
        log_path = find_log_file(td)
        if log_path is None:
            return render_template("partials/error.html", error="No log_*.txt found")
        blocks, parse_err = _safe(parse_log_file, log_path)
        events = None
        events_err = None
        if blocks is not None:
            events, events_err = _safe(pair_events, blocks)
        return render_template(
            "partials/timeline.html",
            blocks=blocks, parse_err=parse_err,
            events=events, events_err=events_err,
        )

    # ── Task graph tab ────────────────────────────────────────────────
    @app.route("/api/task/<project>/<task>/graph")
    def api_graph(project: str, task: str):
        td = _task_path(project, task)
        graph, err = _safe(load_task_graph_with_waves, td)
        return render_template("partials/task_graph.html", graph=graph, error=err, project=project, task=task)

    # ── Subtask detail ────────────────────────────────────────────────
    @app.route("/api/task/<project>/<task>/subtask/<subtask_id>")
    def api_subtask(project: str, task: str, subtask_id: str):
        td = _task_path(project, task)
        subtask_dir = td / subtask_id
        if not subtask_dir.is_dir():
            return render_template("partials/error.html", error=f"Subtask directory not found: {subtask_id}")
        artifacts, art_err = _safe(scan_subtask_artifacts, subtask_dir)

        orch_resp_table = None
        orch_resp_err = None
        orch_resp_html = None
        resp_path = subtask_dir / "orchestrator_responses.md"
        if resp_path.exists():
            orch_resp_table, orch_resp_err = _safe(parse_orchestrator_responses_table, resp_path)
            if orch_resp_table is None:
                orch_resp_html, _ = _safe(load_markdown_rendered, resp_path)

        orch_log_html = None
        orch_leads = None
        log_path = subtask_dir / "orchestrator_log.md"
        if log_path.exists():
            orch_leads, _ = _safe(parse_orchestrator_log_leads, log_path)
            orch_log_html, _ = _safe(load_markdown_rendered, log_path)

        return render_template(
            "partials/subtask.html",
            subtask_id=subtask_id,
            artifacts=artifacts, art_err=art_err,
            orch_resp_table=orch_resp_table, orch_resp_err=orch_resp_err,
            orch_resp_html=orch_resp_html,
            orch_log_html=orch_log_html, orch_leads=orch_leads,
            project=project, task=task,
        )

    # ── Artifact viewer ───────────────────────────────────────────────
    @app.route("/api/task/<project>/<task>/artifact")
    def api_artifact(project: str, task: str):
        td = _task_path(project, task)
        rel_path = request.args.get("path", "")
        if not rel_path:
            return render_template("partials/error.html", error="No path specified")
        full = (td / rel_path).resolve()
        if not full.is_relative_to(outputs_path.resolve()):
            return render_template("partials/error.html", error="Path outside outputs directory")
        if not full.exists():
            return render_template("partials/error.html", error=f"File not found: {rel_path}")

        fm = None
        html_content = None
        err = None
        if full.suffix == ".md":
            fm, _ = _safe(parse_frontmatter, full)
            html_content, err = _safe(load_markdown_rendered, full)
        else:
            try:
                html_content = f"<pre>{full.read_text(encoding='utf-8')}</pre>"
            except Exception:
                err = traceback.format_exc()

        return render_template(
            "partials/artifact.html",
            frontmatter=fm[0] if fm else None,
            content=html_content, error=err,
            filename=full.name,
        )

    return app
