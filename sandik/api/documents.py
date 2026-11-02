# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Devis, factures, avoirs et tableau de bord."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import Client, Document
from ..schemas import ActionIn, DocumentIn, dump_document
from ..services import documents as svc
from .auth import require_user

router = APIRouter(prefix="/api", tags=["documents"], dependencies=[Depends(require_user)])


def _get(db: Session, doc_id: int) -> Document:
    doc = db.get(Document, doc_id, options=[selectinload(Document.lines), selectinload(Document.client)])
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    return doc


def _payload(data: DocumentIn) -> dict:
    payload = data.model_dump(exclude_unset=True, exclude={"type"})
    if data.lines is not None:
        payload["lines"] = [line.model_dump() for line in data.lines]
    return payload


@router.get("/documents")
def list_documents(type: str | None = None, status: str | None = None, client_id: int | None = None,
                   q: str = "", db: Session = Depends(get_db)):
    stmt = select(Document).options(selectinload(Document.client)).order_by(Document.id.desc())
    if type:
        stmt = stmt.where(Document.type == type)
    if status:
        stmt = stmt.where(Document.status == status)
    if client_id:
        stmt = stmt.where(Document.client_id == client_id)
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.join(Client).where(or_(func.lower(Document.number).like(like),
                                           func.lower(Document.title).like(like),
                                           func.lower(Client.name).like(like)))
    return [dump_document(d, full=False) for d in db.scalars(stmt).unique()]


@router.post("/documents", status_code=201)
def create_document(data: DocumentIn, request: Request, db: Session = Depends(get_db)):
    if not data.type:
        raise HTTPException(status_code=422, detail="Type de document manquant.")
    doc = svc.create_document(db, request.app.state.edition, data.type, _payload(data))
    db.flush()
    request.app.state.modules.emit("document.created", db=db, document=doc)
    db.commit()
    return dump_document(doc)


@router.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    return dump_document(_get(db, doc_id))


@router.put("/documents/{doc_id}")
def update_document(doc_id: int, data: DocumentIn, request: Request, db: Session = Depends(get_db)):
    doc = svc.update_document(db, request.app.state.edition, _get(db, doc_id), _payload(data))
    request.app.state.modules.emit("document.updated", db=db, document=doc)
    db.commit()
    return dump_document(doc)


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = _get(db, doc_id)
    if "delete" not in svc.allowed_actions(doc):
        raise HTTPException(status_code=409, detail="Un document émis ne peut pas être supprimé.")
    db.delete(doc)
    db.commit()
    return {"deleted": True}


@router.post("/documents/{doc_id}/actions/{action}")
def document_action(doc_id: int, action: str, request: Request, data: ActionIn | None = None,
                    db: Session = Depends(get_db)):
    doc = _get(db, doc_id)
    params = data.model_dump() if data else {}
    result = svc.run_action(db, request.app.state.edition, doc, action, params, request.app.state.modules)
    db.commit()
    return dump_document(_get(db, result.id))


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    today = date.today()
    year_start = date(today.year, 1, 1)
    docs = list(db.scalars(select(Document).options(selectinload(Document.client))))

    def total(items, attr="total_ht") -> str:
        return format(sum((getattr(d, attr) for d in items), Decimal("0")), "f")

    quotes_open = [d for d in docs if d.type == "quote" and d.status in {"draft", "sent"}]
    quotes_won = [d for d in docs if d.type == "quote" and d.status == "accepted"
                  and d.decided_at and d.decided_at.date() >= year_start]
    unpaid = [d for d in docs if d.type == "invoice" and d.status == "issued"]
    overdue = [d for d in unpaid if d.due_date and d.due_date < today]
    invoiced = [d for d in docs if d.type == "invoice" and d.status in {"issued", "paid"}
                and d.issue_date and d.issue_date >= year_start]
    credits = [d for d in docs if d.type == "credit_note" and d.status == "issued"
               and d.issue_date and d.issue_date >= year_start]
    revenue = sum((d.total_ht for d in invoiced), Decimal("0")) - sum((d.total_ht for d in credits), Decimal("0"))
    recent = sorted(docs, key=lambda d: d.updated_at, reverse=True)[:8]
    return {
        "year": today.year,
        "revenue_ht": format(revenue, "f"),
        "quotes_open": {"count": len(quotes_open), "total_ht": total(quotes_open)},
        "quotes_won": {"count": len(quotes_won), "total_ht": total(quotes_won)},
        "unpaid": {"count": len(unpaid), "total_ttc": total(unpaid, "total_ttc")},
        "overdue": {"count": len(overdue), "total_ttc": total(overdue, "total_ttc")},
        "recent": [dump_document(d, full=False) for d in recent],
    }
