# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Construit l'application autonome (PyInstaller, dossier dist/<nom>/) pour Windows ou Linux.

    python packaging/build_app.py --name sandik --edition sandik --icon sandik/editions/sandik/favicon.ico
    python packaging/build_app.py --name BatiPilot --edition batipilot --icon ... --package batipilot

Prérequis : `pip install . pyinstaller` (et `pywebview` sous Windows pour la fenêtre native).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LAUNCHER = '''\
# Lanceur généré par packaging/build_app.py
import os, sys
os.environ.setdefault("SANDIK_EDITION", {edition!r})
if sys.stdout is None or sys.stderr is None:  # application fenêtrée (pas de console) : journal dans un fichier
    from platformdirs import user_log_dir
    log_dir = user_log_dir({folder!r}, appauthor=False)
    os.makedirs(log_dir, exist_ok=True)
    log = open(os.path.join(log_dir, "application.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stdout or log
    sys.stderr = sys.stderr or log
from sandik.__main__ import main
args = sys.argv[1:]
if "--server" in args:
    args.remove("--server")
elif "--desktop" not in args:
    args.insert(0, "--desktop")
main(args)
'''


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--edition", required=True)
    p.add_argument("--icon", required=True)
    p.add_argument("--package", action="append", default=[], help="paquet Python supplémentaire (ex. batipilot)")
    p.add_argument("--windowed", action="store_true", help="sans console (Windows)")
    p.add_argument("--legal-dir", help="dossier contenant LICENSE, NOTICE.md… (défaut : racine de sandik)")
    args = p.parse_args()

    root = Path(__file__).resolve().parent.parent
    build = root / "build"
    build.mkdir(exist_ok=True)
    launcher = build / f"launcher_{args.edition}.py"
    launcher.write_text(LAUNCHER.format(edition=args.edition, folder=args.edition), encoding="utf-8")

    sep = ";" if sys.platform == "win32" else ":"
    opts = [
        # chemins absolus : PyInstaller résout les chemins relatifs depuis --specpath (build/)
        str(launcher), "--noconfirm", "--clean", "--onedir", "--name", args.name, "--icon", str(Path(args.icon).resolve()),
        "--distpath", str(root / "dist"), "--workpath", str(build / "pyinstaller"), "--specpath", str(build),
        "--collect-data", "sandik", "--copy-metadata", "sandik", "--collect-submodules", "sandik",
        "--collect-submodules", "uvicorn", "--hidden-import", "platformdirs",
    ]
    legal = Path(args.legal_dir).resolve() if args.legal_dir else root
    for name in ("LICENSE", "LICENSE.md", "NOTICE.md", "DISCLAIMER.md", "THIRD_PARTY_NOTICES.md"):
        if (legal / name).is_file():
            opts += ["--add-data", f"{legal / name}{sep}."]
    if (legal / "licenses").is_dir():
        opts += ["--add-data", f"{legal / 'licenses'}{sep}licenses"]
    for pkg in args.package:
        opts += ["--collect-data", pkg, "--copy-metadata", pkg, "--collect-submodules", pkg]
    if args.windowed:
        opts.append("--windowed")
    try:
        import webview  # noqa: F401

        opts += ["--collect-all", "webview"]
    except ImportError:
        pass
    try:  # nom sur le réseau local (mDNS), facultatif
        import zeroconf  # noqa: F401

        opts += ["--collect-submodules", "zeroconf", "--hidden-import", "ifaddr"]
    except ImportError:
        pass

    import PyInstaller.__main__

    PyInstaller.__main__.run(opts)


if __name__ == "__main__":
    main()
