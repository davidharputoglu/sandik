@echo off
REM Essayer sandik sur Windows sans installateur (Python 3.10+ requis : https://www.python.org).
REM Double-cliquez sur ce fichier. Pour BatiPilot : essayer-windows.bat batipilot
cd /d "%~dp0\.."
if not exist .venv (
  echo Creation de l'environnement Python...
  py -3 -m venv .venv || python -m venv .venv
  .venv\Scripts\python -m pip install --upgrade pip
  .venv\Scripts\python -m pip install -e . pywebview
  if exist ..\batipilot\pyproject.toml .venv\Scripts\python -m pip install -e ..\batipilot
)
set SANDIK_EDITION=%1
if "%SANDIK_EDITION%"=="" set SANDIK_EDITION=sandik
.venv\Scripts\python -m sandik --desktop
