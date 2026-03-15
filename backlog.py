#!/usr/bin/env python3
"""backlog — Personal vision management CLI.

Capture, track and grow ideas from voice to reality.
Designed for OpenClaw integration via Telegram/WhatsApp.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from rich.console import Console  # noqa: E402
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

DATA_FILE = Path(__file__).parent / "ideas.json"
BACKLOG_MD = Path(__file__).parent / "BACKLOG.md"
TELEGRAM_MAX_CHARS = 4096

STATUS_ORDER = ["new", "researching", "in-progress", "done", "archived"]
STATUS_EMOJI = {
    "new": "💡",
    "researching": "🔍",
    "in-progress": "🚧",
    "done": "✅",
    "archived": "📦",
}
PRIORITY_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
}

console = Console(force_terminal=True)


# ── Storage ──────────────────────────────────────────────────────────────

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


# ── Commands ─────────────────────────────────────────────────────────────

def cmd_add(args) -> None:
    """Add a new idea."""
    data = load_ideas()
    now = datetime.now(timezone.utc).isoformat()
    idea = {
        "id": next_id(data),
        "title": args.title,
        "description": args.description or "",
        "status": "new",
        "priority": args.priority or "medium",
        "tags": [t.strip() for t in args.tags.split(",")] if args.tags else [],
        "notes": [],
        "source": args.source or "manual",
        "reminder_date": args.reminder or None,
        "created_at": now,
        "updated_at": now,
    }
    data["ideas"].append(idea)
    save_ideas(data)
    console.print(f"[green]✓[/green] Idea [bold]{idea['id']}[/bold] added: {idea['title']}")


def cmd_list(args) -> None:
    """List all ideas as a rich table."""
    data = load_ideas()
    ideas = data["ideas"]

    if args.status:
        ideas = [i for i in ideas if i["status"] == args.status]

    if not ideas:
        console.print("[dim]No ideas found.[/dim]")
        return

    # Sort by status order, then priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    ideas.sort(key=lambda i: (
        STATUS_ORDER.index(i["status"]) if i["status"] in STATUS_ORDER else 99,
        priority_order.get(i["priority"], 1),
    ))

    table = Table(title="Backlog", show_lines=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("P", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Tags", style="dim")
    table.add_column("Reminder", style="yellow", no_wrap=True)
    table.add_column("Created", style="dim", no_wrap=True)

    for idea in ideas:
        status = f"{STATUS_EMOJI.get(idea['status'], '?')} {idea['status']}"
        priority = PRIORITY_EMOJI.get(idea["priority"], "?")
        tags = ", ".join(idea.get("tags", []))
        reminder = idea.get("reminder_date") or ""
        created = idea["created_at"][:10]
        table.add_row(idea["id"], status, priority, idea["title"], tags, reminder, created)

    console.print(table)


def cmd_show(args) -> None:
    """Show details of a single idea."""
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        return

    lines = [
        f"[bold]{idea['title']}[/bold]",
        "",
        f"Status:   {STATUS_EMOJI.get(idea['status'], '?')} {idea['status']}",
        f"Priority: {PRIORITY_EMOJI.get(idea['priority'], '?')} {idea['priority']}",
        f"Source:   {idea.get('source', 'manual')}",
        f"Tags:     {', '.join(idea.get('tags', [])) or '—'}",
        f"Reminder: {idea.get('reminder_date') or '—'}",
        f"Created:  {idea['created_at'][:10]}",
        f"Updated:  {idea['updated_at'][:10]}",
    ]

    if idea.get("description"):
        lines += ["", f"[dim]{idea['description']}[/dim]"]

    if idea.get("notes"):
        lines += ["", "[bold]Notes:[/bold]"]
        for note in idea["notes"]:
            lines.append(f"  [{note['date'][:10]}] {note['text']}")

    console.print(Panel("\n".join(lines), title=f"[dim]{idea['id']}[/dim]", border_style="blue"))


def cmd_update(args) -> None:
    """Update an idea's status, priority or reminder."""
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        return

    changed = []
    if args.status:
        if args.status not in STATUS_ORDER:
            console.print(f"[red]Invalid status. Use: {', '.join(STATUS_ORDER)}[/red]")
            return
        idea["status"] = args.status
        changed.append(f"status → {args.status}")
    if args.priority:
        idea["priority"] = args.priority
        changed.append(f"priority → {args.priority}")
    if args.reminder:
        idea["reminder_date"] = args.reminder
        changed.append(f"reminder → {args.reminder}")
    if args.title:
        idea["title"] = args.title
        changed.append(f"title → {args.title}")

    if changed:
        idea["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_ideas(data)
        console.print(f"[green]✓[/green] Updated [bold]{idea['id']}[/bold]: {', '.join(changed)}")
    else:
        console.print("[dim]Nothing to update.[/dim]")


def cmd_note(args) -> None:
    """Add a note to an idea."""
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        return

    note = {
        "date": datetime.now(timezone.utc).isoformat(),
        "text": args.text,
    }
    idea["notes"].append(note)
    idea["updated_at"] = note["date"]
    save_ideas(data)
    console.print(f"[green]✓[/green] Note added to [bold]{idea['id']}[/bold]")


def cmd_delete(args) -> None:
    """Delete an idea."""
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        return

    data["ideas"] = [i for i in data["ideas"] if i["id"] != args.id]
    save_ideas(data)
    console.print(f"[green]✓[/green] Deleted [bold]{args.id}[/bold]: {idea['title']}")


def cmd_summary(args) -> None:
    """Generate a compact Markdown summary for Telegram/WhatsApp."""
    data = load_ideas()
    md = generate_summary_md(data)
    if args.raw:
        print(md)
    else:
        console.print(Panel(md, title="Telegram Summary", border_style="green"))


def cmd_share(args) -> None:
    """Generate a shareable Markdown card for a single idea."""
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        return

    md = generate_share_md(idea)
    if args.raw:
        print(md)
    else:
        console.print(Panel(md, title="Share Card", border_style="green"))


def cmd_export(args) -> None:
    """Regenerate BACKLOG.md from current data."""
    data = load_ideas()
    generate_backlog_md(data)
    console.print(f"[green]✓[/green] Exported to {BACKLOG_MD}")


# ── Helpers ──────────────────────────────────────────────────────────────

def find_idea(data: dict, idea_id: str) -> dict | None:
    """Find an idea by ID."""
    for idea in data["ideas"]:
        if idea["id"] == idea_id:
            return idea
    console.print(f"[red]Idea {idea_id} not found.[/red]")
    return None


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
            reminder = idea.get("reminder_date") or "—"
            lines.append(f"| {idea['id']} | {p} | {idea['title']} | {tags} | {reminder} |")

        lines.append("")

    BACKLOG_MD.write_text("\n".join(lines), encoding="utf-8")


def generate_summary_md(data: dict) -> str:
    """Generate compact Markdown summary for Telegram (max 4096 chars)."""
    lines = ["📋 *Backlog Summary*", ""]

    active_statuses = ["new", "researching", "in-progress"]
    active = [i for i in data["ideas"] if i["status"] in active_statuses]
    done = [i for i in data["ideas"] if i["status"] == "done"]

    if not active and not done:
        return "📋 *Backlog Summary*\n\nNo ideas yet. Time to brainstorm! 🧠"

    # Count by status
    counts = {}
    for idea in data["ideas"]:
        counts[idea["status"]] = counts.get(idea["status"], 0) + 1
    stats = " | ".join(f"{STATUS_EMOJI.get(s, '')} {c}" for s, c in counts.items())
    lines.append(stats)
    lines.append("")

    # Active ideas
    for status in active_statuses:
        ideas = [i for i in data["ideas"] if i["status"] == status]
        if not ideas:
            continue
        lines.append(f"{STATUS_EMOJI.get(status, '')} *{status.replace('-', ' ').title()}*")
        for idea in ideas:
            p = PRIORITY_EMOJI.get(idea["priority"], "")
            reminder = f" ⏰ {idea['reminder_date']}" if idea.get("reminder_date") else ""
            lines.append(f"  {p} {idea['title']}{reminder}")
        lines.append("")

    # Reminders due
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    reminders = [
        i for i in data["ideas"]
        if i.get("reminder_date") and i["reminder_date"] <= today and i["status"] not in ("done", "archived")
    ]
    if reminders:
        lines.append("⏰ *Reminders Due*")
        for idea in reminders:
            lines.append(f"  → {idea['title']} ({idea['reminder_date']})")
        lines.append("")

    result = "\n".join(lines)
    if len(result) > TELEGRAM_MAX_CHARS:
        result = result[:TELEGRAM_MAX_CHARS - 20] + "\n\n_...truncated_"
    return result


def generate_share_md(idea: dict) -> str:
    """Generate a shareable Markdown card for a single idea."""
    lines = [
        f"💡 *{idea['title']}*",
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
        lines.append(f"Reminder: ⏰ {idea['reminder_date']}")

    lines.append(f"Created: {idea['created_at'][:10]}")

    if idea.get("notes"):
        lines.append("")
        lines.append("📝 *Notes:*")
        for note in idea["notes"]:
            lines.append(f"  [{note['date'][:10]}] {note['text']}")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="backlog",
        description="Personal vision management — capture, track and grow ideas.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="Add a new idea")
    p_add.add_argument("title", help="Idea title")
    p_add.add_argument("description", nargs="?", default="", help="Idea description")
    p_add.add_argument("--priority", "-p", choices=["low", "medium", "high"], default="medium")
    p_add.add_argument("--tags", "-t", help="Comma-separated tags")
    p_add.add_argument("--source", "-s", default="manual", help="Source (manual, voice, openclaw)")
    p_add.add_argument("--reminder", "-r", help="Reminder date (YYYY-MM-DD)")

    # list
    p_list = sub.add_parser("list", help="List all ideas")
    p_list.add_argument("--status", choices=STATUS_ORDER, help="Filter by status")

    # show
    p_show = sub.add_parser("show", help="Show idea details")
    p_show.add_argument("id", help="Idea ID")

    # update
    p_update = sub.add_parser("update", help="Update an idea")
    p_update.add_argument("id", help="Idea ID")
    p_update.add_argument("--status", choices=STATUS_ORDER)
    p_update.add_argument("--priority", choices=["low", "medium", "high"])
    p_update.add_argument("--reminder", help="Reminder date (YYYY-MM-DD)")
    p_update.add_argument("--title", help="New title")

    # note
    p_note = sub.add_parser("note", help="Add a note to an idea")
    p_note.add_argument("id", help="Idea ID")
    p_note.add_argument("text", help="Note text")

    # delete
    p_del = sub.add_parser("delete", help="Delete an idea")
    p_del.add_argument("id", help="Idea ID")

    # summary (for Telegram)
    p_summary = sub.add_parser("summary", help="Compact summary for Telegram/WhatsApp")
    p_summary.add_argument("--raw", action="store_true", help="Output raw Markdown without formatting")

    # share (for Telegram)
    p_share = sub.add_parser("share", help="Shareable card for a single idea")
    p_share.add_argument("id", help="Idea ID")
    p_share.add_argument("--raw", action="store_true", help="Output raw Markdown without formatting")

    # export
    sub.add_parser("export", help="Regenerate BACKLOG.md")

    args = parser.parse_args()

    commands = {
        "add": cmd_add,
        "list": cmd_list,
        "show": cmd_show,
        "update": cmd_update,
        "note": cmd_note,
        "delete": cmd_delete,
        "summary": cmd_summary,
        "share": cmd_share,
        "export": cmd_export,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
