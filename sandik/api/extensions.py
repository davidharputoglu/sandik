# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Gestion des modules : liste, import d'une archive .zip, activation, suppression."""

from __future__ import annotations

import shutil

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..modules import MODULE_ID, install_archive
from ..services.settings_store import get_setting, set_setting
from .auth import require_user

router = APIRouter(prefix="/api/modules-admin", tags=["modules"])
MAX_SIZE = 20 * 1024 * 1024


def require_admin(request: Request, user: User | None = Depends(require_user)) -> User | None:
    if request.app.state.settings.auth and (user is None or user.role != "admin"):
        raise HTTPException(status_code=403, detail={"code": "admin_only", "message": "Réservé à l'administrateur."})
    return user


def _error(code: str, message: str, status: int = 422) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message, "details": [], "params": {}})


@router.get("")
def list_modules(request: Request, _=Depends(require_user)):
    ctx = request.app.state.modules
    loaded = [{**m, "active": True} for m in ctx.describe()]
    skipped = [{**m, "active": False, "menu": []} for m in ctx.skipped]
    pending = []
    known = {m["id"] for m in loaded + skipped}
    for folder in sorted(request.app.state.modules_dir.iterdir()):
        if folder.is_dir() and not folder.name.startswith(".") and folder.name not in known:
            pending.append({"id": folder.name, "name": folder.name, "origin": "imported", "active": False,
                            "reason": "restart", "menu": []})
    return {"modules": loaded + skipped + pending}


@router.post("/import")
async def import_module(request: Request, _=Depends(require_admin)):
    data = await request.body()
    if not data:
        raise _error("module_import.empty", "Fichier vide.")
    if len(data) > MAX_SIZE:
        raise _error("module_import.too_big", "Archive trop volumineuse (20 Mo maximum).")
    try:
        info = install_archive(data, request.app.state.modules_dir, request.app.state.edition)
    except ValueError as exc:
        raise _error(str(exc), "Archive de module invalide.") from exc
    return {**info, "restart_required": True}


@router.post("/{module_id}/toggle")
def toggle_module(module_id: str, request: Request, db: Session = Depends(get_db), _=Depends(require_admin)):
    ed = request.app.state.edition
    cfg = get_setting(db, ed, "modules")
    disabled = set(cfg.get("disabled", []))
    disabled.symmetric_difference_update({module_id})
    set_setting(db, ed, "modules", {"disabled": sorted(disabled)})
    return {"disabled": module_id in disabled, "restart_required": True}


@router.delete("/{module_id}")
def delete_module(module_id: str, request: Request, _=Depends(require_admin)):
    if not MODULE_ID.match(module_id):
        raise HTTPException(status_code=404)
    folder = request.app.state.modules_dir / module_id
    if not folder.is_dir():
        raise _error("module_import.not_imported", "Seuls les modules importés peuvent être supprimés ici.", 409)
    shutil.rmtree(folder)
    return {"deleted": True, "restart_required": True}
