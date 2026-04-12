"""Parse YAML frontmatter from worker/validator markdown files."""

from __future__ import annotations

from pathlib import Path

import yaml


def parse_frontmatter(md_path: Path) -> tuple[dict, str]:
    """Split a markdown file into (yaml_dict, body_markdown).

    Worker frontmatter: role, model, copy, prompt_hash
    Validator frontmatter: role, worker_model, control_model, copy,
        prompt_hash, worker_file, validation_status
    """
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text

    # Find closing ---
    end = text.find("---", 3)
    if end == -1:
        return {}, text

    yaml_str = text[3:end].strip()
    body = text[end + 3:].strip()
    try:
        fm = yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, body


def scan_subtask_artifacts(subtask_dir: Path) -> dict:
    """Scan a subtask directory for workers/ and validators/ and metadata.

    Returns {
        workers: [{path, name, frontmatter}],
        validators: [{path, name, frontmatter}],
    }
    """
    workers = []
    validators = []

    workers_dir = subtask_dir / "workers"
    if workers_dir.is_dir():
        for f in sorted(workers_dir.glob("worker-*.md")):
            fm, _ = parse_frontmatter(f)
            workers.append({"path": f, "name": f.name, "frontmatter": fm})

    validators_dir = subtask_dir / "validators"
    if validators_dir.is_dir():
        for f in sorted(validators_dir.glob("validator-*.md")):
            fm, _ = parse_frontmatter(f)
            validators.append({"path": f, "name": f.name, "frontmatter": fm})

    return {"workers": workers, "validators": validators}
