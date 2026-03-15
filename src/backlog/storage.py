"""Storage and data management for backlog ideas."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path


def _find_data_dir() -> Path:
    """Find the data directory (repo root with ideas.json)."""
    # When installed editable: src/backlog/storage.py -> ../../ideas.json
    candidate = Path(__file__).resolve().parent.parent.parent / "ideas.json"
    if candidate.exists():
        return candidate.parent
    # Fallback: current working directory
    return Path.cwd()


DATA_DIR = _find_data_dir()
DATA_FILE = DATA_DIR / "ideas.json"
BACKLOG_MD = DATA_DIR / "BACKLOG.md"

STATUS_ORDER = ["new", "researching", "in-progress", "done", "archived"]
STATUS_EMOJI = {
    "new": "\U0001f4a1",
    "researching": "\U0001f50d",
    "in-progress": "\U0001f6a7",
    "done": "\u2705",
    "archived": "\U0001f4e6",
}
PRIORITY_EMOJI = {"low": "\U0001f7e2", "medium": "\U0001f7e1", "high": "\U0001f534"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

TELEGRAM_MAX_CHARS = 4096


def load_ideas() -> dict:
    """Load ideas from JSON file."""
    if not DATA_FILE.exists():
        return {"ideas": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_ideas(data: dict) -> None:
    """Save ideas to JSON and regenerate BACKLOG.md."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    generate_backlog_md(data)


def next_id(data: dict) -> str:
    """Generate next idea ID based on today's date."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    existing = [i["id"] for i in data["ideas"] if i["id"].startswith(today)]
    seq = len(existing) + 1
    return f"{today}-{seq:03d}"


def find_idea(data: dict, idea_id: str) -> dict | None:
    """Find an idea by ID."""
    for idea in data["ideas"]:
        if idea["id"] == idea_id:
            return idea
    return None


def extract_tags_from_title(title: str) -> list[str]:
    """Extract #hashtags from title. Title stays unchanged."""
    return [m.lower() for m in re.findall(r"#(\w+)", title)]


# ── Markdown Export ──────────────────────────────────────────────────────


def generate_backlog_md(data: dict) -> None:
    """Generate BACKLOG.md from current ideas."""
    lines = ["# Backlog", ""]
    lines.append(f"*Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC*")
    lines.append("")

    if not data["ideas"]:
        lines.append("*No ideas yet.*")
        BACKLOG_MD.write_text("\n".join(lines), encoding="utf-8")
        return

    for status in STATUS_ORDER:
        ideas = [i for i in data["ideas"] if i["status"] == status]
        if not ideas:
            continue

        lines.append(f"## {STATUS_EMOJI.get(status, '')} {status.replace('-', ' ').title()}")
        lines.append("")
        lines.append("| ID | P | Title | Tags | Reminder |")
        lines.append("|---|---|---|---|---|")

        for idea in ideas:
            p = PRIORITY_EMOJI.get(idea["priority"], "?")
            tags = ", ".join(idea.get("tags", []))
            reminder = idea.get("reminder_date") or "\u2014"
            lines.append(f"| {idea['id']} | {p} | {idea['title']} | {tags} | {reminder} |")

        lines.append("")

    BACKLOG_MD.write_text("\n".join(lines), encoding="utf-8")


def generate_summary_md(data: dict) -> str:
    """Generate compact Markdown summary for Telegram (max 4096 chars)."""
    lines = ["\U0001f4cb *Backlog Summary*", ""]

    active_statuses = ["new", "researching", "in-progress"]
    active = [i for i in data["ideas"] if i["status"] in active_statuses]
    done = [i for i in data["ideas"] if i["status"] == "done"]

    if not active and not done:
        return "\U0001f4cb *Backlog Summary*\n\nNo ideas yet. Time to brainstorm! \U0001f9e0"

    counts: dict[str, int] = {}
    for idea in data["ideas"]:
        counts[idea["status"]] = counts.get(idea["status"], 0) + 1
    stats = " | ".join(f"{STATUS_EMOJI.get(s, '')} {c}" for s, c in counts.items())
    lines.append(stats)
    lines.append("")

    for status in active_statuses:
        ideas = [i for i in data["ideas"] if i["status"] == status]
        if not ideas:
            continue
        lines.append(f"{STATUS_EMOJI.get(status, '')} *{status.replace('-', ' ').title()}*")
        for idea in ideas:
            p = PRIORITY_EMOJI.get(idea["priority"], "")
            reminder = f" \u23f0 {idea['reminder_date']}" if idea.get("reminder_date") else ""
            lines.append(f"  {p} {idea['title']}{reminder}")
        lines.append("")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    reminders = [
        i for i in data["ideas"]
        if i.get("reminder_date") and i["reminder_date"] <= today and i["status"] not in ("done", "archived")
    ]
    if reminders:
        lines.append("\u23f0 *Reminders Due*")
        for idea in reminders:
            lines.append(f"  \u2192 {idea['title']} ({idea['reminder_date']})")
        lines.append("")

    result = "\n".join(lines)
    if len(result) > TELEGRAM_MAX_CHARS:
        result = result[:TELEGRAM_MAX_CHARS - 20] + "\n\n_...truncated_"
    return result


def generate_share_md(idea: dict) -> str:
    """Generate a shareable Markdown card for a single idea."""
    lines = [
        f"\U0001f4a1 *{idea['title']}*",
        "",
    ]

    if idea.get("description"):
        lines.append(idea["description"])
        lines.append("")

    lines.append(f"Status: {STATUS_EMOJI.get(idea['status'], '?')} {idea['status']}")
    lines.append(f"Priority: {PRIORITY_EMOJI.get(idea['priority'], '?')} {idea['priority']}")

    if idea.get("tags"):
        lines.append(f"Tags: {', '.join(idea['tags'])}")
    if idea.get("reminder_date"):
        lines.append(f"Reminder: \u23f0 {idea['reminder_date']}")

    lines.append(f"Created: {idea['created_at'][:10]}")

    if idea.get("notes"):
        lines.append("")
        lines.append("\U0001f4dd *Notes:*")
        for note in idea["notes"]:
            lines.append(f"  [{note['date'][:10]}] {note['text']}")

    return "\n".join(lines)
