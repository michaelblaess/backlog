# backlog

Personal vision management — capture, track and grow ideas from voice to reality.

Designed for [OpenClaw](https://openclaw.com) integration via Telegram/WhatsApp.

## Features

- Capture ideas via CLI (or OpenClaw voice input)
- Track status: `new` → `researching` → `in-progress` → `done` → `archived`
- Priority levels, tags, notes, reminder dates
- Auto-generated `BACKLOG.md` for GitHub visibility
- Telegram/WhatsApp-ready Markdown export (`summary`, `share`)

## Usage

```bash
pip install rich

# Add an idea
python backlog.py add "My idea" "Description" --priority high --tags "tag1,tag2"

# Add via OpenClaw (voice source)
python backlog.py add "Idea from voice" --source openclaw

# List all ideas
python backlog.py list
python backlog.py list --status new

# Show details
python backlog.py show 20260315-001

# Update status/priority/reminder
python backlog.py update 20260315-001 --status researching
python backlog.py update 20260315-001 --reminder 2026-04-01

# Add notes
python backlog.py note 20260315-001 "Research result: ..."

# Telegram summary (all active ideas)
python backlog.py summary --raw

# Share single idea (for Telegram/WhatsApp)
python backlog.py share 20260315-001 --raw

# Regenerate BACKLOG.md
python backlog.py export
```

## Data

Ideas are stored in `ideas.json`. The `BACKLOG.md` file is auto-generated on every change.

## License

MIT
