# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Emplacement des données et langue (assistant de premier lancement, mode bureau)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import write_config
from ..db import get_db
from ..services import network
from ..services.settings_store import get_setting, set_setting
from .extensions import require_admin

router = APIRouter(prefix="/api/system", tags=["system"])


class NetworkIn(BaseModel):
    public_url: str | None = None
    local_name: str | None = None
    mdns: bool | None = None
    dyndns_enabled: bool | None = None
    dyndns_provider: str | None = None
    duckdns_subdomain: str | None = None
    duckdns_token: str | None = None
    dyndns_url: str | None = None


DYNDNS_KEYS = ("dyndns_enabled", "dyndns_provider", "duckdns_subdomain", "duckdns_token", "dyndns_url")


def network_config(app) -> dict:
    """Réglages réseau effectifs : variables d'environnement d'abord, puis Paramètres → Réseau."""
    s = app.state.settings
    with app.state.sessionmaker() as db:
        cfg = get_setting(db, app.state.edition, "network")
    return {
        "public_url": s.public_url or (cfg.get("public_url") or "").rstrip("/"),
        "public_url_locked": bool(s.public_url),
        "local_name": s.local_name or cfg.get("local_name") or app.state.edition.id,
        "local_name_locked": bool(s.local_name),
        "mdns": s.mdns if s.mdns is not None else bool(cfg.get("mdns")),
        "mdns_locked": s.mdns is not None,
        **{k: cfg.get(k) for k in DYNDNS_KEYS},
    }


def apply_dyndns(app) -> None:
    with app.state.sessionmaker() as db:
        cfg = get_setting(db, app.state.edition, "network")
    app.state.dyndns.configure(network.dyndns_url(cfg))


def apply_local_name(app) -> None:
    cfg = network_config(app)
    if cfg["mdns"]:
        app.state.announcer.start(cfg["local_name"], app.state.settings.port, app.state.edition.name)
    else:
        app.state.announcer.stop()


def _network_status(app) -> dict:
    s, ann = app.state.settings, app.state.announcer
    cfg = network_config(app)
    lan_open = s.host not in {"127.0.0.1", "localhost", "::1"}
    return {
        **cfg,
        "port": s.port,
        "desktop": s.desktop,
        "docker": network.in_docker(),
        "lan_open": lan_open,
        "addresses": [f"http://{ip}:{s.port}" for ip in network.local_ipv4()] if lan_open else [],
        "this_computer": f"http://127.0.0.1:{s.port}",
        "local_url": f"http://{cfg['local_name']}.local:{s.port}",
        "mdns_available": network.mdns_available(),
        "mdns_active": ann.active,
        "mdns_error": ann.error,
        "duckdns_token": "•" * 8 if cfg.get("duckdns_token") else "",  # jamais renvoyé en clair
        "dyndns_url": "(…)" if cfg.get("dyndns_url") else "",
        "dyndns_active": app.state.dyndns.active,
        "dyndns_last_result": app.state.dyndns.last_result,
        "dyndns_last_time": app.state.dyndns.last_time,
    }


@router.get("/network")
def get_network(request: Request, _=Depends(require_admin)):
    return _network_status(request.app)


@router.put("/network")
def update_network(data: NetworkIn, request: Request, db: Session = Depends(get_db), _=Depends(require_admin)):
    values: dict = {}
    if data.public_url is not None:
        url = data.public_url.strip().rstrip("/")
        if not network.validate_public_url(url):
            raise HTTPException(status_code=422, detail={"code": "network.bad_url", "message": "Adresse invalide.",
                                                          "details": [], "params": {}})
        values["public_url"] = url
    if data.local_name is not None:
        name = data.local_name.strip().lower()
        if not network.validate_local_name(name):
            raise HTTPException(status_code=422, detail={"code": "network.bad_name", "message": "Nom invalide.",
                                                          "details": [], "params": {}})
        values["local_name"] = name
    if data.mdns is not None:
        values["mdns"] = data.mdns
    if data.dyndns_enabled is not None:
        values["dyndns_enabled"] = data.dyndns_enabled
    if data.dyndns_provider in {"duckdns", "custom"}:
        values["dyndns_provider"] = data.dyndns_provider
    if data.duckdns_subdomain is not None:
        sub = data.duckdns_subdomain.strip().lower().removesuffix(".duckdns.org")
        if sub and not network.DUCKDNS_NAME.match(sub):
            raise HTTPException(status_code=422, detail={"code": "network.bad_name", "message": "Nom invalide.",
                                                          "details": [], "params": {}})
        values["duckdns_subdomain"] = sub
    # jetons : laissés tels quels si le formulaire renvoie le masque
    if data.duckdns_token is not None and not data.duckdns_token.startswith("•"):
        values["duckdns_token"] = data.duckdns_token.strip()
    if data.dyndns_url is not None and data.dyndns_url != "(…)":
        if data.dyndns_url and not network.validate_public_url(data.dyndns_url.split("?")[0]):
            raise HTTPException(status_code=422, detail={"code": "network.bad_url", "message": "Adresse invalide.",
                                                          "details": [], "params": {}})
        values["dyndns_url"] = data.dyndns_url.strip()
    set_setting(db, request.app.state.edition, "network", values)
    # adresse publique déduite de DuckDNS si elle n'est pas renseignée
    cfg = network_config(request.app)
    if cfg.get("dyndns_enabled") and cfg.get("dyndns_provider") == "duckdns" and cfg.get("duckdns_subdomain") \
            and not cfg["public_url"] and not cfg["public_url_locked"]:
        set_setting(db, request.app.state.edition, "network",
                    {"public_url": f"https://{cfg['duckdns_subdomain']}.duckdns.org"})
    apply_local_name(request.app)  # appliqué tout de suite, sans redémarrage
    apply_dyndns(request.app)
    return _network_status(request.app)


class LocationIn(BaseModel):
    data_dir: str | None = None
    language: str | None = None


def _folder(request: Request) -> str:
    return request.app.state.settings.config_file.parent.name if request.app.state.settings.config_file else "sandik"


@router.post("/shutdown")
def shutdown(request: Request, _=Depends(require_admin)):
    """Mode bureau uniquement : arrête l'application (bouton « Quitter »)."""
    if not request.app.state.settings.desktop:
        raise HTTPException(status_code=409, detail={"code": "not_desktop", "message": "Mode serveur."})
    import os
    import threading

    threading.Timer(0.4, os._exit, args=(0,)).start()
    return {"ok": True}


@router.get("/location")
def location(request: Request, _=Depends(require_admin)):
    s = request.app.state.settings
    return {"data_dir": str(s.data_dir), "config_file": str(s.config_file or ""), "desktop": s.desktop,
            "can_change": s.desktop and s.database_url.startswith("sqlite"), "language": s.language}


@router.put("/location")
def change_location(data: LocationIn, request: Request, db: Session = Depends(get_db), _=Depends(require_admin)):
    s = request.app.state.settings
    values: dict[str, str] = {}
    if data.language:
        values["language"] = data.language
    restart = False
    if data.data_dir and Path(data.data_dir).expanduser() != s.data_dir:
        if not (s.desktop and s.database_url.startswith("sqlite")):
            raise HTTPException(status_code=409, detail={"code": "location.not_desktop", "message": "Non disponible."})
        target = Path(data.data_dir).expanduser()
        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise HTTPException(status_code=422, detail={"code": "location.invalid", "message": str(exc)}) from exc
        set_setting(db, request.app.state.edition, "setup", {"location_done": True})
        src_db = Path(s.database_url.removeprefix("sqlite:///"))
        dst_db = target / src_db.name
        if src_db.is_file() and not dst_db.exists():  # copie cohérente de la base (API de sauvegarde SQLite)
            with sqlite3.connect(src_db) as src, sqlite3.connect(dst_db) as dst:
                src.backup(dst)
        values["data_dir"] = str(target)
        restart = True
    if values:
        write_config(_folder(request), **values)
    return {"restart_required": restart}
