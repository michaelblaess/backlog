# backlog

<p align="center">
  <img src="docs/flags/gb.svg" height="13" alt=""> <a href="README.md">English</a> ·
  <img src="docs/flags/de.svg" height="13" alt=""> <b>Deutsch</b>
</p>

---

[![Stars](https://img.shields.io/github/stars/michaelblaess/backlog?logo=github&logoColor=white&color=fbbf24)](https://github.com/michaelblaess/backlog/stargazers)
[![Forks](https://img.shields.io/github/forks/michaelblaess/backlog?logo=github&logoColor=white&color=34d399)](https://github.com/michaelblaess/backlog/network/members)
[![Issues](https://img.shields.io/github/issues/michaelblaess/backlog?logo=github&logoColor=white&color=f87171)](https://github.com/michaelblaess/backlog/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/michaelblaess/backlog?logo=github&logoColor=white&color=a78bfa)](https://github.com/michaelblaess/backlog/pulls)

[![Last Commit](https://img.shields.io/github/last-commit/michaelblaess/backlog?logo=git&logoColor=white&color=3b82f6)](https://github.com/michaelblaess/backlog/commits/main)
[![License](https://img.shields.io/badge/license-Apache_2.0-3b82f6)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-3b82f6?logo=python&logoColor=white)](https://www.python.org/)

Persönliches Visionsmanagement — erfasse, verfolge und entwickle Ideen von der Sprachaufnahme bis zur Umsetzung.

Konzipiert für die Integration mit [OpenClaw](https://openclaw.com) über Telegram/WhatsApp.

## Funktionen

- Ideen über die CLI erfassen (oder per OpenClaw-Spracheingabe)
- Status verfolgen: `new` → `researching` → `in-progress` → `done` → `archived`
- Prioritätsstufen, Tags, Notizen, Erinnerungsdaten
- Automatisch generierte `BACKLOG.md` für die Sichtbarkeit auf GitHub
- Telegram-/WhatsApp-fertiger Markdown-Export (`summary`, `share`)

## Verwendung

```bash
pip install rich

# Eine Idee hinzufuegen
python backlog.py add "My idea" "Description" --priority high --tags "tag1,tag2"

# Per OpenClaw hinzufuegen (Sprachquelle)
python backlog.py add "Idea from voice" --source openclaw

# Alle Ideen auflisten
python backlog.py list
python backlog.py list --status new

# Details anzeigen
python backlog.py show 20260315-001

# Status/Prioritaet/Erinnerung aktualisieren
python backlog.py update 20260315-001 --status researching
python backlog.py update 20260315-001 --reminder 2026-04-01

# Notizen hinzufuegen
python backlog.py note 20260315-001 "Research result: ..."

# Telegram-Zusammenfassung (alle aktiven Ideen)
python backlog.py summary --raw

# Einzelne Idee teilen (fuer Telegram/WhatsApp)
python backlog.py share 20260315-001 --raw

# BACKLOG.md neu generieren
python backlog.py export
```

## Daten

Ideen werden in `ideas.json` gespeichert. Die Datei `BACKLOG.md` wird bei jeder Änderung automatisch generiert.

## Lizenz

MIT
