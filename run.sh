#!/usr/bin/env bash
# Backlog - Startskript
# Verwendung: ./run.sh              (startet TUI)
#             ./run.sh add "Idee"   (CLI-Modus)
#             ./run.sh list         (CLI-Modus)
#
# Nutzt die virtuelle Umgebung (.venv) falls vorhanden,
# sonst das globale Python.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [ -x "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" -m backlog "$@"
else
    python3 -m backlog "$@"
fi
