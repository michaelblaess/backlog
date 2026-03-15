"""CLI interface for backlog."""

import argparse
import os
from datetime import datetime, timezone

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from backlog.storage import (
    STATUS_ORDER,
    STATUS_EMOJI,
    PRIORITY_EMOJI,
    load_ideas,
    save_ideas,
    next_id,
    find_idea,
    extract_tags_from_title,
    generate_backlog_md,
    generate_summary_md,
    generate_share_md,
)

console = Console(force_terminal=True)


# ── Commands ─────────────────────────────────────────────────────────────


def cmd_add(args: argparse.Namespace) -> None:
    data = load_ideas()
    now = datetime.now(timezone.utc).isoformat()
    explicit_tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    title_tags = extract_tags_from_title(args.title)
    all_tags = list(dict.fromkeys(explicit_tags + title_tags))
    idea = {
        "id": next_id(data),
        "title": args.title,
        "description": args.description or "",
        "status": "new",
        "priority": args.priority or "medium",
        "tags": all_tags,
        "notes": [],
        "source": args.source or "manual",
        "reminder_date": args.reminder or None,
        "created_at": now,
        "updated_at": now,
    }
    data["ideas"].append(idea)
    save_ideas(data)
    console.print(f"[green]\u2713[/green] Idea [bold]{idea['id']}[/bold] added: {idea['title']}")


def cmd_list(args: argparse.Namespace) -> None:
    data = load_ideas()
    ideas = data["ideas"]

    if args.status:
        ideas = [i for i in ideas if i["status"] == args.status]

    if not ideas:
        console.print("[dim]No ideas found.[/dim]")
        return

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
    table.add_column("N", no_wrap=True)
    table.add_column("Reminder", style="yellow", no_wrap=True)
    table.add_column("Created", style="dim", no_wrap=True)

    for idea in ideas:
        status = f"{STATUS_EMOJI.get(idea['status'], '?')} {idea['status']}"
        priority = PRIORITY_EMOJI.get(idea["priority"], "?")
        tags = ", ".join(idea.get("tags", []))
        notes_count = len(idea.get("notes", []))
        notes_display = f"\U0001f4dd {notes_count}" if notes_count > 0 else ""
        reminder = idea.get("reminder_date") or ""
        created = idea["created_at"][:10]
        table.add_row(idea["id"], status, priority, idea["title"], tags, notes_display, reminder, created)

    console.print(table)


def cmd_show(args: argparse.Namespace) -> None:
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        console.print(f"[red]Idea {args.id} not found.[/red]")
        return

    lines = [
        f"[bold]{idea['title']}[/bold]",
        "",
        f"Status:   {STATUS_EMOJI.get(idea['status'], '?')} {idea['status']}",
        f"Priority: {PRIORITY_EMOJI.get(idea['priority'], '?')} {idea['priority']}",
        f"Source:   {idea.get('source', 'manual')}",
        f"Tags:     {', '.join(idea.get('tags', [])) or '\u2014'}",
        f"Reminder: {idea.get('reminder_date') or '\u2014'}",
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


def cmd_update(args: argparse.Namespace) -> None:
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        console.print(f"[red]Idea {args.id} not found.[/red]")
        return

    changed = []
    if args.status:
        idea["status"] = args.status
        changed.append(f"status \u2192 {args.status}")
    if args.priority:
        idea["priority"] = args.priority
        changed.append(f"priority \u2192 {args.priority}")
    if args.reminder:
        idea["reminder_date"] = args.reminder
        changed.append(f"reminder \u2192 {args.reminder}")
    if args.title:
        idea["title"] = args.title
        changed.append(f"title \u2192 {args.title}")

    if changed:
        idea["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_ideas(data)
        console.print(f"[green]\u2713[/green] Updated [bold]{idea['id']}[/bold]: {', '.join(changed)}")
    else:
        console.print("[dim]Nothing to update.[/dim]")


def cmd_note(args: argparse.Namespace) -> None:
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        console.print(f"[red]Idea {args.id} not found.[/red]")
        return

    note = {"date": datetime.now(timezone.utc).isoformat(), "text": args.text}
    idea["notes"].append(note)
    idea["updated_at"] = note["date"]
    save_ideas(data)
    console.print(f"[green]\u2713[/green] Note added to [bold]{idea['id']}[/bold]")


def cmd_delete(args: argparse.Namespace) -> None:
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        console.print(f"[red]Idea {args.id} not found.[/red]")
        return

    data["ideas"] = [i for i in data["ideas"] if i["id"] != args.id]
    save_ideas(data)
    console.print(f"[green]\u2713[/green] Deleted [bold]{args.id}[/bold]: {idea['title']}")


def cmd_summary(args: argparse.Namespace) -> None:
    data = load_ideas()
    md = generate_summary_md(data)
    if args.raw:
        print(md)
    else:
        console.print(Panel(md, title="Telegram Summary", border_style="green"))


def cmd_share(args: argparse.Namespace) -> None:
    data = load_ideas()
    idea = find_idea(data, args.id)
    if not idea:
        console.print(f"[red]Idea {args.id} not found.[/red]")
        return

    md = generate_share_md(idea)
    if args.raw:
        print(md)
    else:
        console.print(Panel(md, title="Share Card", border_style="green"))


def cmd_export(args: argparse.Namespace) -> None:
    data = load_ideas()
    generate_backlog_md(data)
    console.print("[green]\u2713[/green] Exported to BACKLOG.md")


# ── CLI Parser ───────────────────────────────────────────────────────────


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        prog="backlog",
        description="Personal vision management \u2014 capture, track and grow ideas.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a new idea")
    p_add.add_argument("title", help="Idea title")
    p_add.add_argument("description", nargs="?", default="", help="Idea description")
    p_add.add_argument("--priority", "-p", choices=["low", "medium", "high"], default="medium")
    p_add.add_argument("--tags", "-t", help="Comma-separated tags")
    p_add.add_argument("--source", "-s", default="manual", help="Source (manual, voice, openclaw)")
    p_add.add_argument("--reminder", "-r", help="Reminder date (YYYY-MM-DD)")

    p_list = sub.add_parser("list", help="List all ideas")
    p_list.add_argument("--status", choices=STATUS_ORDER, help="Filter by status")

    p_show = sub.add_parser("show", help="Show idea details")
    p_show.add_argument("id", help="Idea ID")

    p_update = sub.add_parser("update", help="Update an idea")
    p_update.add_argument("id", help="Idea ID")
    p_update.add_argument("--status", choices=STATUS_ORDER)
    p_update.add_argument("--priority", choices=["low", "medium", "high"])
    p_update.add_argument("--reminder", help="Reminder date (YYYY-MM-DD)")
    p_update.add_argument("--title", help="New title")

    p_note = sub.add_parser("note", help="Add a note to an idea")
    p_note.add_argument("id", help="Idea ID")
    p_note.add_argument("text", help="Note text")

    p_del = sub.add_parser("delete", help="Delete an idea")
    p_del.add_argument("id", help="Idea ID")

    p_summary = sub.add_parser("summary", help="Compact summary for Telegram/WhatsApp")
    p_summary.add_argument("--raw", action="store_true", help="Output raw Markdown")

    p_share = sub.add_parser("share", help="Shareable card for a single idea")
    p_share.add_argument("id", help="Idea ID")
    p_share.add_argument("--raw", action="store_true", help="Output raw Markdown")

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
