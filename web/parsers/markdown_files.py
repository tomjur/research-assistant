"""Parse semi-structured markdown files (HYPERPARAMETERS, TODO, USER_PROMPT, orchestrator tables)."""

from __future__ import annotations

import re
from pathlib import Path

import markdown as md


def load_markdown_rendered(path: Path) -> str:
    """Read a markdown file and render to HTML."""
    text = path.read_text(encoding="utf-8")
    # Strip YAML frontmatter if present
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:]
    return md.markdown(text, extensions=["tables", "fenced_code"])


def parse_hyperparameters(path: Path) -> list[tuple[str, str]]:
    """Extract (name, value) pairs from HYPERPARAMETERS.md markdown table."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|-") or line.startswith("| -"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) >= 2:
            name = cells[0].strip("`").strip()
            value = cells[1].strip()
            # Skip header row
            if name.lower() in ("name", ""):
                continue
            rows.append((name, value))
    return rows


def parse_todo_items(path: Path) -> list[dict]:
    """Extract checklist items from TODO.md.

    Returns [{id, text, done, wave}].
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    items: list[dict] = []
    current_wave = ""
    for line in text.splitlines():
        stripped = line.strip()
        # Detect wave headers
        wave_match = re.match(r"^#{1,3}\s+(Wave\s+\d+.*|Stage\s+III.*)$", stripped, re.IGNORECASE)
        if wave_match:
            current_wave = wave_match.group(1).strip()
            continue
        # Detect checkbox items
        cb_match = re.match(r"^-\s+\[([ xX])\]\s+(.+)$", stripped)
        if cb_match:
            done = cb_match.group(1).lower() == "x"
            text_content = cb_match.group(2).strip()
            # Extract task id (backtick-wrapped)
            id_match = re.search(r"`([^`]+)`", text_content)
            task_id = id_match.group(1) if id_match else ""
            items.append({
                "id": task_id,
                "text": text_content,
                "done": done,
                "wave": current_wave,
            })
    return items


def parse_user_prompt_sections(path: Path) -> dict:
    """Parse USER_PROMPT.md into sections.

    Returns {original_request, deliverable_constraints, search_terms_html, raw_html}.
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    current_section = ""
    current_lines: list[str] = []

    for line in text.splitlines():
        heading = re.match(r"^##\s+(.+)$", line)
        if heading:
            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = heading.group(1).strip().lower()
            current_lines = []
        else:
            current_lines.append(line)
    if current_section:
        sections[current_section] = "\n".join(current_lines).strip()

    return {
        "original_request": sections.get("original request", ""),
        "deliverable_constraints": sections.get("deliverable constraints", ""),
        "search_terms_html": md.markdown(
            sections.get("approved search terms (stage i)", ""),
            extensions=["tables"],
        ),
        "raw_html": md.markdown(text, extensions=["tables", "fenced_code"]),
    }


def parse_orchestrator_responses_table(path: Path) -> list[dict] | None:
    """Parse the Copy/Worker/Validator table from orchestrator_responses.md.

    Returns [{copy, worker_path, validator_path}] or None if parsing fails.
    """
    text = path.read_text(encoding="utf-8")
    rows: list[dict] = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table and rows:
                break
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        # Skip header and separator rows
        if cells[0].lower() in ("copy", "") or re.match(r"^-+$", cells[0]):
            in_table = True
            continue
        in_table = True
        # Extract file paths from backtick-wrapped or bare text
        worker_path = re.sub(r"[`\s]", "", cells[1])
        validator_path = re.sub(r"[`\s]", "", cells[2])
        rows.append({
            "copy": cells[0],
            "worker_path": worker_path,
            "validator_path": validator_path,
        })
    return rows if rows else None


def parse_orchestrator_log_leads(path: Path) -> list[dict] | None:
    """Parse ## Related-work leads table from orchestrator_log.md.

    Returns [{lead_summary, source_artifacts, implies_new_subgoal, escalated_to_user, notes}]
    or None if no table found.
    """
    text = path.read_text(encoding="utf-8")
    # Find the related-work leads section
    section_match = re.search(r"##\s+Related-work leads\s*\n([\s\S]*?)(?=\n##|\Z)", text)
    if not section_match:
        return None
    section = section_match.group(1)
    rows: list[dict] = []
    in_table = False
    headers: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table and rows:
                break
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if not in_table:
            headers = [h.lower().replace(" ", "_") for h in cells]
            in_table = True
            continue
        if re.match(r"^[\s|:-]+$", stripped):
            continue
        if len(cells) >= len(headers):
            row = {}
            for i, h in enumerate(headers):
                row[h] = cells[i] if i < len(cells) else ""
            if any(v.strip() for v in row.values()):
                rows.append(row)
    return rows if rows else None
