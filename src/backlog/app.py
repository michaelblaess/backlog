"""backlog TUI — Textual admin console for vision management."""

from datetime import datetime, timezone
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Container
from textual.screen import ModalScreen
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
)

from backlog.storage import (
    STATUS_ORDER,
    STATUS_EMOJI,
    PRIORITY_EMOJI,
    PRIORITY_ORDER,
    load_ideas,
    save_ideas,
    next_id,
    extract_tags_from_title,
)


# ── Detail Screen ────────────────────────────────────────────────────────


class DetailScreen(ModalScreen[None]):
    """Show full details of an idea."""

    BINDINGS = [
        Binding("escape", "cancel", "Close"),
    ]

    def __init__(self, idea: dict) -> None:
        super().__init__()
        self.idea = idea

    def compose(self) -> ComposeResult:
        idea = self.idea
        with Container():
            yield Label(
                f"{STATUS_EMOJI.get(idea['status'], '')} {idea['title']}",
                classes="detail-title",
            )
            yield Label(
                f"ID:        {idea['id']}\n"
                f"Status:    {STATUS_EMOJI.get(idea['status'], '?')} {idea['status']}\n"
                f"Priority:  {PRIORITY_EMOJI.get(idea['priority'], '?')} {idea['priority']}\n"
                f"Source:    {idea.get('source', 'manual')}\n"
                f"Tags:      {', '.join(idea.get('tags', [])) or '\u2014'}\n"
                f"Reminder:  {idea.get('reminder_date') or '\u2014'}\n"
                f"Created:   {idea['created_at'][:10]}\n"
                f"Updated:   {idea['updated_at'][:10]}",
            )
            if idea.get("description"):
                yield Label(idea["description"], classes="detail-description")
            if idea.get("notes"):
                yield Label("Notes:", classes="detail-notes-header")
                for note in idea["notes"]:
                    yield Label(
                        f"  [{note['date'][:10]}] {note['text']}",
                        classes="detail-note",
                    )

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Add Idea Screen ──────────────────────────────────────────────────────


class AddIdeaScreen(ModalScreen[dict | None]):
    """Modal for adding a new idea."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("New Idea", classes="form-title")
            yield Label("Title", classes="form-label")
            yield Input(placeholder="Idea title...", id="title")
            yield Label("Description", classes="form-label")
            yield Input(placeholder="Optional description...", id="description")
            yield Label("Priority", classes="form-label")
            yield Select(
                [(f"{PRIORITY_EMOJI[p]} {p}", p) for p in ["high", "medium", "low"]],
                value="medium",
                id="priority",
            )
            yield Label("Tags (comma-separated)", classes="form-label")
            yield Input(placeholder="tag1, tag2, ...", id="tags")
            yield Label("Reminder (YYYY-MM-DD)", classes="form-label")
            yield Input(placeholder="Optional...", id="reminder")
            yield Label("Enter = Save  |  Escape = Cancel", classes="form-hint")

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        title = self.query_one("#title", Input).value.strip()
        if not title:
            self.notify("Title is required", severity="error")
            return

        description = self.query_one("#description", Input).value.strip()
        priority = self.query_one("#priority", Select).value
        tags_raw = self.query_one("#tags", Input).value.strip()
        reminder = self.query_one("#reminder", Input).value.strip()

        self.dismiss({
            "title": title,
            "description": description,
            "priority": priority if priority != Select.BLANK else "medium",
            "tags": [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else [],
            "reminder_date": reminder or None,
        })

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Add Note Screen ──────────────────────────────────────────────────────


class AddNoteScreen(ModalScreen[str | None]):
    """Modal for adding a note to an idea."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, idea_title: str) -> None:
        super().__init__()
        self.idea_title = idea_title

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(f"Add Note to: {self.idea_title}", classes="form-title")
            yield Input(placeholder="Note text...", id="note-text")
            yield Label("Enter = Save  |  Escape = Cancel", classes="form-hint")

    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = self.query_one("#note-text", Input).value.strip()
        if not text:
            self.notify("Note text is required", severity="error")
            return
        self.dismiss(text)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Status Screen ────────────────────────────────────────────────────────


class StatusScreen(ModalScreen[str | None]):
    """Modal to pick a new status."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current_status: str) -> None:
        super().__init__()
        self.current_status = current_status

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Change Status", classes="form-title")
            yield Select(
                [(f"{STATUS_EMOJI.get(s, '')} {s}", s) for s in STATUS_ORDER],
                value=self.current_status,
                id="status-select",
            )
            yield Label("Select = Save  |  Escape = Cancel", classes="form-hint")

    @on(Select.Changed, "#status-select")
    def on_status_changed(self, event: Select.Changed) -> None:
        if event.value != Select.BLANK and event.value != self.current_status:
            self.dismiss(event.value)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ── Main App ─────────────────────────────────────────────────────────────


class BacklogApp(App):
    """Backlog TUI — Personal vision management."""

    TITLE = "backlog"
    SUB_TITLE = "vision management"
    CSS_PATH = Path(__file__).parent.parent.parent / "app.tcss"

    BINDINGS = [
        Binding("n", "add_idea", "New Idea"),
        Binding("enter", "show_detail", "Detail"),
        Binding("s", "change_status", "Status"),
        Binding("p", "cycle_priority", "Priority"),
        Binding("o", "add_note", "Add Note"),
        Binding("delete", "delete_idea", "Delete", key_display="DEL"),
        Binding("r", "refresh_table", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data: dict = load_ideas()
        self.filter_status: str | None = None
        self.filter_text: str = ""

        try:
            from textual_themes import register_all
            register_all(self)
        except ImportError:
            pass

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="stats-bar")
        with Container(id="filter-bar"):
            with Horizontal():
                yield Select(
                    [("All", "all")]
                    + [(f"{STATUS_EMOJI.get(s, '')} {s}", s) for s in STATUS_ORDER],
                    value="all",
                    id="filter-status",
                    allow_blank=False,
                )
                yield Input(placeholder="Search...", id="filter-search")
        yield DataTable(id="ideas-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#ideas-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_columns("ID", "Status", "P", "Title", "Tags", "N", "Reminder", "Created")
        self._refresh_data()

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if len(self.screen_stack) > 1:
            return None
        row_actions = ("show_detail", "change_status", "cycle_priority", "add_note", "delete_idea")
        if action in row_actions:
            table = self.query_one("#ideas-table", DataTable)
            if table.row_count == 0:
                return None
        return True

    @on(Select.Changed, "#filter-status")
    def on_filter_status_changed(self, event: Select.Changed) -> None:
        self.filter_status = None if event.value == "all" else event.value
        self._refresh_data()

    @on(Input.Changed, "#filter-search")
    def on_filter_search_changed(self, event: Input.Changed) -> None:
        self.filter_text = event.value.strip().lower()
        self._refresh_data()

    def _refresh_data(self) -> None:
        self.data = load_ideas()
        ideas = self.data["ideas"]

        if self.filter_status:
            ideas = [i for i in ideas if i["status"] == self.filter_status]
        if self.filter_text:
            ideas = [
                i for i in ideas
                if self.filter_text in i["title"].lower()
                or self.filter_text in i.get("description", "").lower()
                or any(self.filter_text in t.lower() for t in i.get("tags", []))
            ]

        ideas.sort(key=lambda i: (
            STATUS_ORDER.index(i["status"]) if i["status"] in STATUS_ORDER else 99,
            PRIORITY_ORDER.get(i["priority"], 1),
        ))

        all_ideas = self.data["ideas"]
        counts: dict[str, int] = {}
        for idea in all_ideas:
            counts[idea["status"]] = counts.get(idea["status"], 0) + 1
        stats_parts = [f"Total: {len(all_ideas)}"]
        for s in STATUS_ORDER:
            if s in counts:
                stats_parts.append(f"{STATUS_EMOJI.get(s, '')} {s}: {counts[s]}")
        self.query_one("#stats-bar", Static).update("  ".join(stats_parts))

        table = self.query_one("#ideas-table", DataTable)
        table.clear()
        for idea in ideas:
            notes_count = len(idea.get("notes", []))
            table.add_row(
                idea["id"],
                f"{STATUS_EMOJI.get(idea['status'], '?')} {idea['status']}",
                PRIORITY_EMOJI.get(idea["priority"], "?"),
                idea["title"],
                ", ".join(idea.get("tags", [])),
                f"\U0001f4dd {notes_count}" if notes_count > 0 else "",
                idea.get("reminder_date") or "",
                idea["created_at"][:10],
                key=idea["id"],
            )
        self.refresh_bindings()

    def _get_selected_idea(self) -> dict | None:
        table = self.query_one("#ideas-table", DataTable)
        if table.row_count == 0:
            return None
        row_data = table.get_row_at(table.cursor_row)
        idea_id = row_data[0]
        for idea in self.data["ideas"]:
            if idea["id"] == idea_id:
                return idea
        return None

    def action_show_detail(self) -> None:
        idea = self._get_selected_idea()
        if idea:
            self.push_screen(DetailScreen(idea))

    def action_add_idea(self) -> None:
        def on_result(result: dict | None) -> None:
            if result is None:
                return
            now = datetime.now(timezone.utc).isoformat()
            title_tags = extract_tags_from_title(result["title"])
            all_tags = list(dict.fromkeys(result["tags"] + title_tags))
            idea = {
                "id": next_id(self.data),
                "title": result["title"],
                "description": result["description"],
                "status": "new",
                "priority": result["priority"],
                "tags": all_tags,
                "notes": [],
                "source": "tui",
                "reminder_date": result["reminder_date"],
                "created_at": now,
                "updated_at": now,
            }
            self.data["ideas"].append(idea)
            save_ideas(self.data)
            self._refresh_data()
            self.notify(f"Added: {idea['title']}")

        self.push_screen(AddIdeaScreen(), callback=on_result)

    def action_change_status(self) -> None:
        idea = self._get_selected_idea()
        if not idea:
            return

        def on_result(new_status: str | None) -> None:
            if new_status is None or new_status == idea["status"]:
                return
            idea["status"] = new_status
            idea["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_ideas(self.data)
            self._refresh_data()
            self.notify(f"{idea['title']} \u2192 {STATUS_EMOJI.get(new_status, '')} {new_status}")

        self.push_screen(StatusScreen(idea["status"]), callback=on_result)

    def action_cycle_priority(self) -> None:
        idea = self._get_selected_idea()
        if not idea:
            return
        cycle = {"low": "medium", "medium": "high", "high": "low"}
        new_priority = cycle.get(idea["priority"], "medium")
        idea["priority"] = new_priority
        idea["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_ideas(self.data)
        self._refresh_data()
        self.notify(f"{idea['title']} \u2192 {PRIORITY_EMOJI.get(new_priority, '')} {new_priority}")

    def action_add_note(self) -> None:
        idea = self._get_selected_idea()
        if not idea:
            return

        def on_result(text: str | None) -> None:
            if text is None:
                return
            note = {"date": datetime.now(timezone.utc).isoformat(), "text": text}
            idea["notes"].append(note)
            idea["updated_at"] = note["date"]
            save_ideas(self.data)
            self._refresh_data()
            self.notify(f"Note added to: {idea['title']}")

        self.push_screen(AddNoteScreen(idea["title"]), callback=on_result)

    def action_delete_idea(self) -> None:
        idea = self._get_selected_idea()
        if not idea:
            return
        title = idea["title"]
        self.data["ideas"] = [i for i in self.data["ideas"] if i["id"] != idea["id"]]
        save_ideas(self.data)
        self._refresh_data()
        self.notify(f"Deleted: {title}")

    def action_refresh_table(self) -> None:
        self._refresh_data()
        self.notify("Refreshed")
