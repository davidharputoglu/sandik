# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Édition (nom, thème, visuels), réglages et champs personnalisés."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import __version__
from ..db import get_db
from ..models import CustomField
from ..schemas import CustomFieldIn, dump_field
from ..services import numbering
from ..services.settings_store import KEYS, get_setting, set_setting
from .auth import require_user

public = APIRouter(tags=["edition"])
router = APIRouter(prefix="/api", tags=["settings"])


@public.get("/api/edition")
def edition_info(request: Request, db: Session = Depends(get_db)):
    ed = request.app.state.edition
    appearance = get_setting(db, ed, "appearance")
    return {
        "id": ed.id,
        "name": ed.name,
        "tagline": ed.tagline,
        "license": ed.license,
        "about": ed.about,
        "version": __version__,
        "theme": ed.theme,
        "themes": ed.themes,
        "appearance": appearance,
        "i18n": {**ed.i18n, "preferred": request.app.state.settings.language},
        "assets": {k: f"/edition/{k}" for k in ed.assets},
        "modules": request.app.state.modules.describe(),
        "desktop": request.app.state.settings.desktop,
    }


@public.get("/edition/{name}")
def edition_asset(name: str, request: Request):
    path = request.app.state.edition.asset_path(name)
    if path is None:
        raise HTTPException(status_code=404)
    return FileResponse(path, headers={"Cache-Control": "public, max-age=3600"})


@public.get("/favicon.ico", include_in_schema=False)
def favicon(request: Request):
    path = request.app.state.edition.asset_path("favicon")
    if path is None:
        raise HTTPException(status_code=404)
    return FileResponse(path)


# ---------------------------------------------------------------- réglages
@router.get("/settings")
def all_settings(request: Request, db: Session = Depends(get_db), _=Depends(require_user)):
    ed = request.app.state.edition
    out = {key: get_setting(db, ed, key) for key in sorted(KEYS)}
    out["company"]["has_logo"] = _logo_path(request) is not None
    return out


@router.put("/settings/{key}")
def update_setting(key: str, data: dict[str, Any], request: Request, db: Session = Depends(get_db),
                   _=Depends(require_user)):
    ed = request.app.state.edition
    if key not in KEYS:
        raise HTTPException(status_code=404, detail="Réglage inconnu.")
    if key == "numbering":
        merged = {**get_setting(db, ed, "numbering"), **data}
        errors = []
        for doc_type in ("quote", "invoice", "credit_note"):
            errors += [f"{doc_type} : {e}" for e in numbering.validate_pattern(merged[doc_type], merged["reset"])]
        if merged["reset"] not in {"yearly", "monthly", "never"}:
            errors.append("Remise à zéro : yearly, monthly ou never.")
        if errors:
            raise HTTPException(status_code=422, detail={"message": "Format de numérotation invalide.", "details": errors})
    return set_setting(db, ed, key, data)


LOGO_TYPES = {b"\x89PNG": ("png", "image/png"), b"\xff\xd8\xff": ("jpg", "image/jpeg"), b"RIFF": ("webp", "image/webp")}


def _logo_path(request: Request):
    folder = request.app.state.settings.data_dir / "uploads"
    return next((p for p in folder.glob("company-logo.*")), None) if folder.is_dir() else None


@router.get("/company/logo")
def company_logo(request: Request, _=Depends(require_user)):
    path = _logo_path(request)
    if path is None:
        raise HTTPException(status_code=404)
    return FileResponse(path, headers={"Cache-Control": "no-cache"})


@router.put("/company/logo")
async def upload_company_logo(request: Request, _=Depends(require_user)):
    """Logo de l'entreprise utilisatrice (affiché sur ses devis et factures) : PNG, JPEG ou WebP."""
    data = await request.body()
    kind = next((v for magic, v in LOGO_TYPES.items() if data.startswith(magic)), None)
    if kind is None or len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=422, detail={"code": "logo.invalid", "message": "Image PNG, JPEG ou WebP de 5 Mo maximum."})
    folder = request.app.state.settings.data_dir / "uploads"
    folder.mkdir(exist_ok=True)
    for old in folder.glob("company-logo.*"):
        old.unlink()
    (folder / f"company-logo.{kind[0]}").write_bytes(data)
    return {"ok": True}


@router.delete("/company/logo")
def delete_company_logo(request: Request, _=Depends(require_user)):
    path = _logo_path(request)
    if path:
        path.unlink()
    return {"ok": True}


@router.get("/numbering/preview")
def numbering_preview(pattern: str, _=Depends(require_user)):
    return {"preview": numbering.preview(pattern)}


# ---------------------------------------------------------------- champs personnalisés
@router.get("/custom-fields")
def list_fields(request: Request, entity: str | None = None, db: Session = Depends(get_db), _=Depends(require_user)):
    q = select(CustomField).order_by(CustomField.entity, CustomField.position, CustomField.id)
    if entity:
        q = q.where(CustomField.entity == entity)
    fields = [dump_field(f) for f in db.scalars(q)]
    for spec in request.app.state.modules.fields:
        if entity in (None, spec.entity):
            fields.append({**spec.__dict__, "id": None, "position": 999})
    return fields


@router.post("/custom-fields", status_code=201)
def create_field(data: CustomFieldIn, db: Session = Depends(get_db), _=Depends(require_user)):
    if db.scalar(select(CustomField).where(CustomField.entity == data.entity, CustomField.key == data.key)):
        raise HTTPException(status_code=409, detail="Un champ avec cette clé existe déjà.")
    field = CustomField(**data.model_dump())
    db.add(field)
    db.commit()
    return dump_field(field)


@router.put("/custom-fields/{field_id}")
def update_field(field_id: int, data: CustomFieldIn, db: Session = Depends(get_db), _=Depends(require_user)):
    field = db.get(CustomField, field_id)
    if not field:
        raise HTTPException(status_code=404)
    for k, v in data.model_dump(exclude={"entity", "key"}).items():
        setattr(field, k, v)
    db.commit()
    return dump_field(field)


@router.delete("/custom-fields/{field_id}", status_code=204)
def delete_field(field_id: int, db: Session = Depends(get_db), _=Depends(require_user)):
    field = db.get(CustomField, field_id)
    if field:
        db.delete(field)
        db.commit()
