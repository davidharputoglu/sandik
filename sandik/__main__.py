# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Lancement : ``sandik`` (serveur) ou ``sandik --desktop`` (poste de travail)."""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
import socket
import threading
import time
import urllib.request
import webbrowser

import uvicorn

from .app import create_app
from .config import load_settings

DEFAULT_PORT = 8460


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _running_edition(port: int) -> str | None:
    """Édition déjà lancée sur ce port (pour ne pas démarrer deux fois l'application de bureau)."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as r:
            return json.loads(r.read()).get("edition")
    except Exception:
        return None


def _uvicorn_options(settings) -> dict:
    # En-têtes X-Forwarded-* des relais web de confiance (Caddy, Traefik, Nginx Proxy Manager…)
    return {"proxy_headers": True, "forwarded_allow_ips": settings.trusted_proxies}


def _desktop_window(app, host: str, port: int, title: str) -> bool:
    """Fenêtre native (pywebview) si disponible. Renvoie False pour revenir au navigateur."""
    if os.environ.get("SANDIK_BROWSER"):
        return False
    try:
        import webview  # pywebview : fenêtre native (Edge WebView2 sous Windows)
    except Exception:
        return False
    server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning",
                                           **_uvicorn_options(app.state.settings)))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    try:
        webview.create_window(title, f"http://{host}:{port}/", width=1360, height=880, min_size=(980, 640))
        webview.start()
    except Exception:
        logging.getLogger("sandik").exception("Fenêtre native indisponible, ouverture du navigateur")
        webbrowser.open(f"http://{host}:{port}/")
        while True:
            time.sleep(3600)
    server.should_exit = True
    return True


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="sandik", description="CRM, devis et factures.")
    p.add_argument("--edition", help="Édition à lancer (sandik, batipilot, ...) ou dossier d'édition.")
    p.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute (0.0.0.0 pour Docker / réseau).")
    p.add_argument("--port", type=int, help=f"port d'écoute (défaut : SANDIK_PORT ou {DEFAULT_PORT})")
    p.add_argument("--data-dir", help="Dossier des données (base SQLite, fichiers).")
    p.add_argument("--database-url", help="Ex. postgresql+psycopg://utilisateur:motdepasse@hote/base")
    p.add_argument("--desktop", action="store_true", help="Mode poste de travail : fenêtre de l'application, sans connexion.")
    p.add_argument("--no-browser", action="store_true", help="Mode bureau sans ouvrir de fenêtre ni de navigateur.")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
    settings = load_settings(edition=args.edition, data_dir=args.data_dir, database_url=args.database_url,
                             desktop=args.desktop, port=args.port, host=args.host)
    log = logging.getLogger("sandik")

    port = settings.port
    if args.desktop:
        from .editions import load_edition

        edition_id = load_edition(settings.edition).id
        if _running_edition(port) == edition_id:  # déjà ouverte : on affiche simplement l'application
            webbrowser.open(f"http://127.0.0.1:{port}/")
            return
        while not _port_free(args.host, port):
            port += 1

    settings = dataclasses.replace(settings, port=port)
    app = create_app(settings)
    log.info("Données : %s", settings.data_dir)
    if args.desktop and not args.no_browser:
        if _desktop_window(app, args.host, port, app.state.edition.name):
            return
        threading.Timer(1.5, webbrowser.open, args=(f"http://{args.host}:{port}/",)).start()
    uvicorn.run(app, host=args.host, port=port, log_level="info", **_uvicorn_options(settings))


if __name__ == "__main__":
    main()
