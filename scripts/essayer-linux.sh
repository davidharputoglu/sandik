#!/usr/bin/env bash
# Essayer sandik sur Linux sans installateur (Python 3.10+). BatiPilot : ./essayer-linux.sh batipilot
set -e
cd "$(dirname "$0")/.."
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -e .
  [[ -f ../batipilot/pyproject.toml ]] && .venv/bin/pip install -e ../batipilot
fi
SANDIK_EDITION="${1:-sandik}" exec .venv/bin/python -m sandik --desktop
