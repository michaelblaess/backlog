@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM  Backlog - Setup
REM  Richtet eine virtuelle Umgebung ein und installiert alles.
REM  Voraussetzung: Python 3.10+ muss installiert sein.
REM ============================================================

echo.
echo  +----------------------------------------------+
echo  :   Backlog - Setup                             :
echo  +----------------------------------------------+
echo.

REM --- Python pruefen ---
python --version >nul 2>&1
if errorlevel 1 (
    echo  [FEHLER] Python wurde nicht gefunden!
    echo  Bitte Python 3.10+ installieren: https://www.python.org/downloads/
    echo  WICHTIG: Bei der Installation "Add Python to PATH" ankreuzen!
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER% gefunden
echo.

REM --- Virtuelle Umgebung erstellen ---
set VENV_DIR=%~dp0.venv

if exist "%VENV_DIR%\Scripts\python.exe" (
    echo  [OK] Virtuelle Umgebung existiert bereits
) else (
    echo  Erstelle virtuelle Umgebung...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo  [FEHLER] Konnte virtuelle Umgebung nicht erstellen!
        pause
        exit /b 1
    )
    echo  [OK] Virtuelle Umgebung erstellt
)
echo.

REM --- pip upgrade ---
echo  Aktualisiere pip...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --quiet
echo  [OK] pip aktualisiert
echo.

REM --- Paket installieren ---
echo  Installiere Backlog + Abhaengigkeiten...
"%VENV_DIR%\Scripts\pip.exe" install -e "%~dp0." --quiet
if errorlevel 1 (
    echo  [FEHLER] Installation fehlgeschlagen!
    pause
    exit /b 1
)
echo  [OK] Backlog installiert
echo.

REM --- Fertig ---
echo  +----------------------------------------------+
echo  :   Setup abgeschlossen!                        :
echo  :                                                :
echo  :   TUI starten:                                 :
echo  :     run.bat                                    :
echo  :                                                :
echo  :   CLI verwenden:                               :
echo  :     run.bat add "Meine Idee"                   :
echo  :     run.bat list                               :
echo  :     run.bat summary --raw                      :
echo  :                                                :
echo  +----------------------------------------------+
echo.
pause
