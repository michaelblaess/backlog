"""Tests for backlog storage module."""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from backlog.storage import (
    STATUS_ORDER,
    STATUS_EMOJI,
    PRIORITY_EMOJI,
    load_ideas,
    save_ideas,
    next_id,
    find_idea,
    extract_tags_from_title,
    generate_summary_md,
    generate_share_md,
    generate_backlog_md,
    TELEGRAM_MAX_CHARS,
)


@pytest.fixture
def empty_data() -> dict:
    return {"ideas": []}


@pytest.fixture
def sample_idea() -> dict:
    return {
        "id": "20260315-001",
        "title": "Test Idea",
        "description": "A test idea description",
        "status": "new",
        "priority": "high",
        "tags": ["test", "python"],
        "notes": [],
        "source": "manual",
        "reminder_date": None,
        "created_at": "2026-03-15T10:00:00+00:00",
        "updated_at": "2026-03-15T10:00:00+00:00",
    }


@pytest.fixture
def sample_data(sample_idea: dict) -> dict:
    return {"ideas": [sample_idea]}


@pytest.fixture
def data_file(tmp_path: Path) -> Path:
    f = tmp_path / "ideas.json"
    f.write_text('{"ideas": []}', encoding="utf-8")
    return f


class TestLoadIdeas:
    def test_load_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / "ideas.json"
        f.write_text('{"ideas": []}', encoding="utf-8")
        with patch("backlog.storage.DATA_FILE", f):
            data = load_ideas()
        assert data == {"ideas": []}

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        f = tmp_path / "nonexistent.json"
        with patch("backlog.storage.DATA_FILE", f):
            data = load_ideas()
        assert data == {"ideas": []}

    def test_load_with_ideas(self, tmp_path: Path, sample_data: dict) -> None:
        f = tmp_path / "ideas.json"
        f.write_text(json.dumps(sample_data), encoding="utf-8")
        with patch("backlog.storage.DATA_FILE", f):
            data = load_ideas()
        assert len(data["ideas"]) == 1
        assert data["ideas"][0]["title"] == "Test Idea"


class TestSaveIdeas:
    def test_save_creates_file(self, tmp_path: Path, sample_data: dict) -> None:
        f = tmp_path / "ideas.json"
        md = tmp_path / "BACKLOG.md"
        with patch("backlog.storage.DATA_FILE", f), patch("backlog.storage.BACKLOG_MD", md):
            save_ideas(sample_data)
        assert f.exists()
        loaded = json.loads(f.read_text(encoding="utf-8"))
        assert len(loaded["ideas"]) == 1

    def test_save_generates_backlog_md(self, tmp_path: Path, sample_data: dict) -> None:
        f = tmp_path / "ideas.json"
        md = tmp_path / "BACKLOG.md"
        with patch("backlog.storage.DATA_FILE", f), patch("backlog.storage.BACKLOG_MD", md):
            save_ideas(sample_data)
        assert md.exists()
        content = md.read_text(encoding="utf-8")
        assert "Test Idea" in content

    def test_save_preserves_unicode(self, tmp_path: Path) -> None:
        f = tmp_path / "ideas.json"
        md = tmp_path / "BACKLOG.md"
        data = {"ideas": [{
            "id": "20260315-001",
            "title": "Umlaut-Test: aerger",
            "description": "",
            "status": "new",
            "priority": "medium",
            "tags": [],
            "notes": [],
            "source": "manual",
            "reminder_date": None,
            "created_at": "2026-03-15T10:00:00+00:00",
            "updated_at": "2026-03-15T10:00:00+00:00",
        }]}
        with patch("backlog.storage.DATA_FILE", f), patch("backlog.storage.BACKLOG_MD", md):
            save_ideas(data)
        content = f.read_text(encoding="utf-8")
        assert "aerger" in content


class TestNextId:
    def test_first_id_of_day(self, empty_data: dict) -> None:
        idea_id = next_id(empty_data)
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        assert idea_id == f"{today}-001"

    def test_sequential_ids(self) -> None:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        data = {"ideas": [
            {"id": f"{today}-001"},
            {"id": f"{today}-002"},
        ]}
        idea_id = next_id(data)
        assert idea_id == f"{today}-003"

    def test_different_day_resets(self) -> None:
        data = {"ideas": [
            {"id": "20260101-001"},
            {"id": "20260101-002"},
        ]}
        idea_id = next_id(data)
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        assert idea_id == f"{today}-001"


class TestFindIdea:
    def test_find_existing(self, sample_data: dict) -> None:
        idea = find_idea(sample_data, "20260315-001")
        assert idea is not None
        assert idea["title"] == "Test Idea"

    def test_find_nonexistent(self, sample_data: dict) -> None:
        idea = find_idea(sample_data, "99999999-999")
        assert idea is None

    def test_find_in_empty(self, empty_data: dict) -> None:
        idea = find_idea(empty_data, "20260315-001")
        assert idea is None


class TestGenerateSummaryMd:
    def test_empty_summary(self, empty_data: dict) -> None:
        md = generate_summary_md(empty_data)
        assert "No ideas yet" in md

    def test_summary_includes_titles(self, sample_data: dict) -> None:
        md = generate_summary_md(sample_data)
        assert "Test Idea" in md

    def test_summary_shows_priority(self, sample_data: dict) -> None:
        md = generate_summary_md(sample_data)
        assert PRIORITY_EMOJI["high"] in md

    def test_summary_shows_reminder(self) -> None:
        data = {"ideas": [{
            "id": "20260315-001",
            "title": "Reminder Test",
            "description": "",
            "status": "new",
            "priority": "medium",
            "tags": [],
            "notes": [],
            "source": "manual",
            "reminder_date": "2026-03-20",
            "created_at": "2026-03-15T10:00:00+00:00",
            "updated_at": "2026-03-15T10:00:00+00:00",
        }]}
        md = generate_summary_md(data)
        assert "2026-03-20" in md

    def test_summary_respects_telegram_limit(self) -> None:
        ideas = []
        for i in range(200):
            ideas.append({
                "id": f"20260315-{i:03d}",
                "title": f"Idea with a really long title number {i} to fill up space quickly",
                "description": "",
                "status": "new",
                "priority": "medium",
                "tags": ["tag1", "tag2", "tag3"],
                "notes": [],
                "source": "manual",
                "reminder_date": None,
                "created_at": "2026-03-15T10:00:00+00:00",
                "updated_at": "2026-03-15T10:00:00+00:00",
            })
        data = {"ideas": ideas}
        md = generate_summary_md(data)
        assert len(md) <= TELEGRAM_MAX_CHARS


class TestGenerateShareMd:
    def test_share_includes_title(self, sample_idea: dict) -> None:
        md = generate_share_md(sample_idea)
        assert "Test Idea" in md

    def test_share_includes_status(self, sample_idea: dict) -> None:
        md = generate_share_md(sample_idea)
        assert "new" in md

    def test_share_includes_tags(self, sample_idea: dict) -> None:
        md = generate_share_md(sample_idea)
        assert "test, python" in md

    def test_share_includes_description(self, sample_idea: dict) -> None:
        md = generate_share_md(sample_idea)
        assert "A test idea description" in md

    def test_share_includes_notes(self) -> None:
        idea = {
            "id": "20260315-001",
            "title": "Note Test",
            "description": "",
            "status": "new",
            "priority": "medium",
            "tags": [],
            "notes": [{"date": "2026-03-15T12:00:00+00:00", "text": "Research done"}],
            "source": "manual",
            "reminder_date": None,
            "created_at": "2026-03-15T10:00:00+00:00",
            "updated_at": "2026-03-15T10:00:00+00:00",
        }
        md = generate_share_md(idea)
        assert "Research done" in md

    def test_share_without_description(self) -> None:
        idea = {
            "id": "20260315-001",
            "title": "No Desc",
            "description": "",
            "status": "done",
            "priority": "low",
            "tags": [],
            "notes": [],
            "source": "manual",
            "reminder_date": None,
            "created_at": "2026-03-15T10:00:00+00:00",
            "updated_at": "2026-03-15T10:00:00+00:00",
        }
        md = generate_share_md(idea)
        assert "No Desc" in md


class TestGenerateBacklogMd:
    def test_empty_backlog(self, tmp_path: Path) -> None:
        md = tmp_path / "BACKLOG.md"
        with patch("backlog.storage.BACKLOG_MD", md):
            generate_backlog_md({"ideas": []})
        content = md.read_text(encoding="utf-8")
        assert "No ideas yet" in content

    def test_backlog_groups_by_status(self, tmp_path: Path) -> None:
        md = tmp_path / "BACKLOG.md"
        data = {"ideas": [
            {
                "id": "20260315-001", "title": "New One", "status": "new",
                "priority": "high", "tags": [], "reminder_date": None,
                "created_at": "2026-03-15T10:00:00+00:00",
                "updated_at": "2026-03-15T10:00:00+00:00",
            },
            {
                "id": "20260315-002", "title": "Done One", "status": "done",
                "priority": "low", "tags": [], "reminder_date": None,
                "created_at": "2026-03-15T10:00:00+00:00",
                "updated_at": "2026-03-15T10:00:00+00:00",
            },
        ]}
        with patch("backlog.storage.BACKLOG_MD", md):
            generate_backlog_md(data)
        content = md.read_text(encoding="utf-8")
        assert "New" in content
        assert "Done" in content
        # New should appear before Done
        assert content.index("New") < content.index("Done")


class TestExtractTagsFromTitle:
    def test_leading_hashtag_removed(self) -> None:
        title, tags = extract_tags_from_title("#Sitefinity: gesperrte Seiten entsperren")
        assert title == "gesperrte Seiten entsperren"
        assert tags == ["sitefinity"]

    def test_leading_hashtag_without_colon(self) -> None:
        title, tags = extract_tags_from_title("#Python neues Widget bauen")
        assert title == "neues Widget bauen"
        assert tags == ["python"]

    def test_multiple_hashtags_only_leading_removed(self) -> None:
        title, tags = extract_tags_from_title("#Python: neues #TUI Widget bauen")
        assert title == "neues #TUI Widget bauen"
        assert tags == ["python", "tui"]

    def test_no_hashtags(self) -> None:
        title, tags = extract_tags_from_title("Einfacher Titel ohne Tags")
        assert title == "Einfacher Titel ohne Tags"
        assert tags == []

    def test_hashtag_lowercase(self) -> None:
        title, tags = extract_tags_from_title("#React App bauen")
        assert tags == ["react"]

    def test_mid_sentence_hashtag_stays(self) -> None:
        title, tags = extract_tags_from_title("Fix fuer #Sitefinity Bug")
        assert title == "Fix fuer #Sitefinity Bug"
        assert tags == ["sitefinity"]

    def test_only_hashtag_keeps_title(self) -> None:
        title, tags = extract_tags_from_title("#onlytag")
        assert title == "#onlytag"
        assert tags == ["onlytag"]


class TestStatusConstants:
    def test_all_statuses_have_emoji(self) -> None:
        for status in STATUS_ORDER:
            assert status in STATUS_EMOJI

    def test_all_priorities_have_emoji(self) -> None:
        for priority in ["low", "medium", "high"]:
            assert priority in PRIORITY_EMOJI

    def test_status_order_complete(self) -> None:
        assert len(STATUS_ORDER) == 5
        assert "new" in STATUS_ORDER
        assert "done" in STATUS_ORDER
        assert "archived" in STATUS_ORDER
