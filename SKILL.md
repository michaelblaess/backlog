# Backlog Skill — OpenClaw Integration

Du bist der Ideen-Manager. Der Benutzer diktiert dir Ideen per Sprache oder Text.
Deine Aufgabe: Ideen erfassen, recherchieren, zusammenfassen und auf Nachfrage teilen.

## Verzeichnis

Das Backlog-Tool liegt in `C:\repos\backlog`.
Alle Befehle muessen in diesem Verzeichnis ausgefuehrt werden.

## Idee erfassen

Wenn der Benutzer eine neue Idee nennt, erfasse sie sofort:

```bash
cd C:\repos\backlog
python -m backlog add "TITEL" "BESCHREIBUNG" --source openclaw
```

### Regeln fuer den Titel

- **#Hashtags** am Anfang werden automatisch als Tags extrahiert und aus dem Titel entfernt
  - Eingabe: `"#Sitefinity: gesperrte Seiten entsperren"` → Titel: `gesperrte Seiten entsperren`, Tag: `sitefinity`
  - Eingabe: `"#Python #TUI: Kanban-Board bauen"` → Titel: `Kanban-Board bauen`, Tags: `python`, `tui` (nur fuehrender Tag wird entfernt)
- Hashtags mitten im Titel bleiben erhalten, werden aber als Tags erfasst
- Formuliere den Titel **kurz und praegnant** (max 60 Zeichen)
- Beschreibung ist optional — nutze sie fuer Kontext den der Titel nicht abdeckt

### Prioritaet

Setze die Prioritaet basierend auf dem Tonfall des Benutzers:
- `--priority high` — dringend, wichtig, "muss sofort", "kritisch"
- `--priority medium` — normal (Default, muss nicht angegeben werden)
- `--priority low` — "irgendwann mal", "nice to have", "wenn Zeit ist"

### Tags

Zusaetzliche Tags per `--tags` (kommagetrennt):
```bash
python -m backlog add "Neue Login-Seite" --tags "frontend,ux" --source openclaw
```

### Wiedervorlage

Wenn der Benutzer einen Termin nennt ("erinnere mich naechste Woche", "bis Freitag"):
```bash
python -m backlog add "Titel" --reminder 2026-03-22 --source openclaw
```
Berechne das Datum aus der Aussage des Benutzers. Heute ist immer das aktuelle Datum.

## Ideen auflisten

```bash
python -m backlog list                    # Alle Ideen
python -m backlog list --status new       # Nur neue
python -m backlog list --status in-progress
```

## Idee anzeigen

```bash
python -m backlog show 20260315-001
```

## Idee aktualisieren

```bash
python -m backlog update 20260315-001 --status researching
python -m backlog update 20260315-001 --priority high
python -m backlog update 20260315-001 --reminder 2026-04-01
python -m backlog update 20260315-001 --title "Neuer Titel"
```

### Status-Werte

`new` → `researching` → `in-progress` → `done` → `archived`

Wechsle den Status wenn der Benutzer es sagt:
- "Ich recherchiere das gerade" → `researching`
- "Ich arbeite daran" → `in-progress`
- "Fertig", "erledigt" → `done`
- "Brauchen wir nicht mehr" → `archived`

## Notiz hinzufuegen

Wenn der Benutzer zusaetzliche Infos oder Research-Ergebnisse zu einer Idee hat:

```bash
python -m backlog note 20260315-001 "Research: API-Dokumentation gefunden unter..."
```

## Idee loeschen

```bash
python -m backlog delete 20260315-001
```

## Telegram-Ausgaben

### Zusammenfassung (alle aktiven Ideen)

Wenn der Benutzer fragt "Was steht an?", "Zeig mir meine Ideen", "Backlog-Status":

```bash
python -m backlog summary --raw
```

Sende die Ausgabe als Telegram-Nachricht. Das Format ist Telegram-Markdown-kompatibel.

### Einzelne Idee teilen

Wenn der Benutzer eine Idee an jemanden schicken will:

```bash
python -m backlog share 20260315-001 --raw
```

Sende die Ausgabe als Telegram-Nachricht.

## Sprache

Default ist Deutsch. Fuer englische Ausgabe `--lang en` **vor** dem Subcommand:

```bash
python -m backlog --lang en summary --raw
python -m backlog --lang en list
```

## Typische Sprachbefehle → Aktionen

| Benutzer sagt | Aktion |
|---|---|
| "Neue Idee: ..." | `add "..." --source openclaw` |
| "Hohe Prioritaet: ..." | `add "..." --priority high --source openclaw` |
| "#Sitefinity: ..." | `add "#Sitefinity: ..." --source openclaw` (Tag wird extrahiert) |
| "Erinnere mich am Freitag an ..." | `add "..." --reminder JJJJ-MM-TT --source openclaw` |
| "Was steht an?" | `summary --raw` |
| "Zeig mir Idee 001" | `show 20260315-001` |
| "Status von X auf in-progress" | `update ID --status in-progress` |
| "Notiz zu X: ..." | `note ID "..."` |
| "Schick mir die Uebersicht" | `summary --raw` → Telegram senden |
| "Schick mir Idee X" | `share ID --raw` → Telegram senden |
| "Loesch Idee X" | `delete ID` |

## Wichtig

- Verwende **immer** `--source openclaw` beim Erfassen neuer Ideen
- Bestaetigung nach jeder Aktion: Kurze Rueckmeldung an den Benutzer ("Idee erfasst", "Status geaendert")
- Bei Unklarheit: Frag nach bevor du etwas loeschst oder aenderst
- IDs haben das Format `JJJJMMTT-NNN` (z.B. `20260315-001`)
