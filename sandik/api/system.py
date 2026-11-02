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
from ..services.settings_store import set_setting
from .extensions import require_admin

router = APIRouter(prefix="/api/system", tags=["system"])


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
