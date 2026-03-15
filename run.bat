@echo off
REM Backlog - Startskript
REM Verwendung: run.bat              (startet TUI)
REM             run.bat add "Idee"   (CLI-Modus)
REM             run.bat list         (CLI-Modus)
REM
REM Nutzt die virtuelle Umgebung (.venv) falls vorhanden,
REM sonst das globale Python.

set VENV_PYTHON=%~dp0.venv\Scripts\python.exe

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -m backlog %*
) else (
    python -m backlog %*
)
