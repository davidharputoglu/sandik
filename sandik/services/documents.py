# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Règles métier des devis, factures et avoirs."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..editions import Edition
from ..models import Client, Document, DocumentLine
from . import numbering
from .settings_store import get_setting
from .totals import compute_totals

TYPES = ("quote", "invoice", "credit_note")
LABELS = {"quote": "Devis", "invoice": "Facture", "credit_note": "Avoir"}
EDITABLE = {"quote": {"draft", "sent"}, "invoice": {"draft"}, "credit_note": {"draft"}}
LINE_FIELDS = (
    "kind", "article_id", "reference", "label", "description", "quantity", "unit",
    "unit_price", "discount_percent", "vat_rate",
)
DOC_FIELDS = (
    "title", "valid_until", "due_date", "operation_nature", "vat_on_debits", "vat_exemption_text",
    "delivery_address", "intro", "notes", "terms", "extra",
)


class BusinessError(Exception):
    """Règle métier non respectée.

    ``code`` : identifiant traduit par l'interface (clé ``errors.<code>``) ;
    ``message`` : texte français de secours ; ``details`` : codes des points à corriger.
    """

    def __init__(self, code: str, message: str, details: list[str] | None = None, params: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []
        self.params = params or {}


def now() -> datetime:
    return datetime.now(timezone.utc)


def is_editable(doc: Document) -> bool:
    return doc.status in EDITABLE[doc.type]


def allowed_actions(doc: Document) -> list[str]:
    t, s = doc.type, doc.status
    actions: list[str] = []
    if is_editable(doc):
        actions += ["edit", "delete"]
    if t == "quote":
        if s == "draft":
            actions.append("send")
        if s in {"draft", "sent"}:
            actions += ["accept", "refuse"]
        if s == "accepted":
            actions.append("to_invoice")
        if s == "refused":
            actions.append("reopen")
    elif t == "invoice":
        if s == "draft":
            actions.append("issue")
        if s == "issued":
            actions.append("mark_paid")
        if s == "paid":
            actions.append("mark_unpaid")
        if s in {"issued", "paid"}:
            actions.append("credit_note")
    elif t == "credit_note" and s == "draft":
        actions.append("issue")
    if t != "credit_note":
        actions.append("duplicate")
    return actions


def _vat_exempt(vat_settings: dict) -> bool:
    return vat_settings.get("regime") == "franchise"


def set_lines(doc: Document, lines: list[dict[str, Any]], vat_settings: dict) -> None:
    exempt = _vat_exempt(vat_settings)
    doc.lines.clear()
    for i, data in enumerate(lines):
        line = DocumentLine(position=i)
        for f in LINE_FIELDS:
            if f in data and data[f] is not None:
                setattr(line, f, data[f])
        if exempt:
            line.vat_rate = Decimal("0")
        doc.lines.append(line)
    refresh_totals(doc)


def refresh_totals(doc: Document) -> None:
    totals = compute_totals(doc.lines)
    doc.total_ht = totals["total_ht"]
    doc.total_vat = totals["total_vat"]
    doc.total_ttc = totals["total_ttc"]
    doc.vat_breakdown = totals["vat_breakdown"]


def apply_fields(doc: Document, data: dict[str, Any]) -> None:
    for f in DOC_FIELDS:
        if f in data and data[f] is not None:
            setattr(doc, f, data[f])


def create_document(db: Session, edition: Edition, doc_type: str, data: dict[str, Any]) -> Document:
    if doc_type not in TYPES:
        raise BusinessError("doc.unknown_type", "Type de document inconnu.")
    client = db.get(Client, data.get("client_id"))
    if client is None:
        raise BusinessError("doc.client_required", "Choisissez un client.")
    docs_cfg = get_setting(db, edition, "documents")
    vat_cfg = get_setting(db, edition, "vat")
    doc = Document(type=doc_type, status="draft", client=client, extra={})
    doc.operation_nature = docs_cfg.get("default_operation_nature", "services")
    doc.vat_on_debits = bool(docs_cfg.get("vat_on_debits", False))
    apply_fields(doc, data)
    if _vat_exempt(vat_cfg) and not doc.vat_exemption_text:
        doc.vat_exemption_text = vat_cfg.get("franchise_text", "")
    if doc_type == "quote":
        # Les devis sont numérotés dès leur création (la loi n'impose pas de continuité pour les devis).
        doc.issue_date = data.get("issue_date") or date.today()
        doc.valid_until = doc.valid_until or doc.issue_date + timedelta(days=int(docs_cfg["quote_validity_days"]))
        doc.number = numbering.next_number(db, "quote", get_setting(db, edition, "numbering"), doc.issue_date)
        if not doc.intro:
            doc.intro = docs_cfg.get("quote_intro", "")
    if not doc.terms and doc_type == "invoice":
        doc.terms = default_terms(docs_cfg)
    set_lines(doc, data.get("lines") or [], vat_cfg)
    db.add(doc)
    return doc


def default_terms(docs_cfg: dict) -> str:
    days = docs_cfg.get("payment_terms_days", 30)
    parts = [
        docs_cfg.get("payment_terms_text", "").replace("{jours}", str(days)),
        docs_cfg.get("early_payment_text", ""),
        docs_cfg.get("late_penalty_text", ""),
    ]
    return "\n".join(p for p in parts if p)


def update_document(db: Session, edition: Edition, doc: Document, data: dict[str, Any]) -> Document:
    if not is_editable(doc):
        raise BusinessError("doc.locked", "Ce document n'est plus modifiable. Pour corriger une facture émise, faites un avoir.")
    if data.get("client_id") and data["client_id"] != doc.client_id:
        client = db.get(Client, data["client_id"])
        if client is None:
            raise BusinessError("client.not_found", "Client introuvable.")
        doc.client = client
    if doc.type == "quote" and data.get("issue_date"):
        doc.issue_date = data["issue_date"]
    apply_fields(doc, data)
    if "lines" in data and data["lines"] is not None:
        set_lines(doc, data["lines"], get_setting(db, edition, "vat"))
    return doc


def client_snapshot(client: Client) -> dict[str, Any]:
    keys = ("kind", "name", "contact_name", "email", "phone", "siren", "vat_number",
            "address_line1", "address_line2", "postal_code", "city", "country")
    return {k: getattr(client, k) for k in keys}


def check_issuable(doc: Document, company: dict, client: Client) -> list[str]:
    """Renvoie les codes des informations obligatoires manquantes."""
    missing = []
    for key in ("name", "siren", "address_line1", "postal_code", "city"):
        if not str(company.get(key, "")).strip():
            missing.append(f"company.{key}")
    if not client.address_line1.strip() or not client.city.strip():
        missing.append("client.address")
    if client.kind == "company" and client.country == "FR" and not client.siren.strip():
        missing.append("client.siren")
    if not any(line.kind == "item" for line in doc.lines):
        missing.append("doc.no_lines")
    return missing


def _canonical(doc: Document) -> str:
    payload = {
        "type": doc.type,
        "number": doc.number,
        "issue_date": doc.issue_date,
        "due_date": doc.due_date,
        "client": doc.client_snapshot,
        "issuer": doc.issuer_snapshot,
        "lines": [
            {f: getattr(line, f) for f in LINE_FIELDS if f != "article_id"} | {"total_ht": line.total_ht}
            for line in doc.lines
        ],
        "total_ht": doc.total_ht,
        "total_vat": doc.total_vat,
        "total_ttc": doc.total_ttc,
    }
    return json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)


def issue_document(db: Session, edition: Edition, doc: Document, issue_date: date | None, hooks) -> Document:
    """Émet une facture ou un avoir : numéro définitif, figement, chaînage d'intégrité."""
    if doc.type not in {"invoice", "credit_note"} or doc.status != "draft":
        raise BusinessError("doc.not_issuable", "Seul un brouillon de facture ou d'avoir peut être émis.")
    company = get_setting(db, edition, "company")
    missing = check_issuable(doc, company, doc.client)
    if missing:
        raise BusinessError("doc.missing_info", "Impossible d'émettre ce document, il manque des informations obligatoires.", missing)
    d = issue_date or date.today()
    last = db.execute(
        select(Document)
        .where(Document.type == doc.type, Document.status != "draft", Document.issue_date.is_not(None))
        .order_by(Document.issue_date.desc())
        .limit(1)
    ).scalar_one_or_none()
    if last and last.issue_date and d < last.issue_date:
        raise BusinessError(
            "doc.date_before_last",
            f"La date ne peut pas être antérieure à celle du dernier document émis ({last.issue_date:%d/%m/%Y}).",
            params={"date": last.issue_date.isoformat()},
        )
    hooks.emit("document.before_issue", db=db, document=doc)

    docs_cfg = get_setting(db, edition, "documents")
    doc.issue_date = d
    if doc.type == "invoice" and not doc.due_date:
        doc.due_date = d + timedelta(days=int(docs_cfg["payment_terms_days"]))
    doc.number = numbering.next_number(db, doc.type, get_setting(db, edition, "numbering"), d)
    doc.client_snapshot = client_snapshot(doc.client)
    doc.issuer_snapshot = dict(company)
    refresh_totals(doc)
    previous = db.execute(
        select(Document.integrity_hash)
        .where(Document.type.in_(("invoice", "credit_note")), Document.integrity_hash != "")
        .order_by(Document.issued_at.desc(), Document.id.desc())
        .limit(1)
    ).scalar_one_or_none() or ""
    doc.previous_hash = previous
    doc.integrity_hash = hashlib.sha256((previous + _canonical(doc)).encode("utf-8")).hexdigest()
    doc.status = "issued"
    doc.issued_at = now()
    return doc


def copy_document(db: Session, edition: Edition, src: Document, new_type: str, link: bool) -> Document:
    data = {f: getattr(src, f) for f in DOC_FIELDS}
    data["extra"] = dict(src.extra or {})
    data["client_id"] = src.client_id
    data["lines"] = [{f: getattr(line, f) for f in LINE_FIELDS} for line in src.lines]
    if new_type != src.type or new_type == "quote":
        data["valid_until"] = None
    data["due_date"] = None
    if new_type != "quote":
        data["terms"] = ""
    doc = create_document(db, edition, new_type, data)
    if link:
        doc.source_id = src.id
    return doc


def run_action(db: Session, edition: Edition, doc: Document, action: str, params: dict, hooks) -> Document:
    if action not in allowed_actions(doc):
        raise BusinessError("doc.action_not_allowed", f"Action impossible sur ce document ({LABELS[doc.type].lower()} : {doc.status}).")
    if action == "send":
        doc.status, doc.sent_at = "sent", now()
    elif action == "accept":
        doc.status, doc.decided_at = "accepted", now()
    elif action == "refuse":
        doc.status, doc.decided_at = "refused", now()
    elif action == "reopen":
        doc.status, doc.decided_at = "draft", None
    elif action == "to_invoice":
        return copy_document(db, edition, doc, "invoice", link=True)
    elif action == "credit_note":
        return copy_document(db, edition, doc, "credit_note", link=True)
    elif action == "duplicate":
        return copy_document(db, edition, doc, doc.type, link=False)
    elif action == "issue":
        issue_document(db, edition, doc, params.get("issue_date"), hooks)
        hooks.emit("document.issued", db=db, document=doc)
    elif action == "mark_paid":
        doc.status, doc.paid_at = "paid", params.get("paid_at") or date.today()
    elif action == "mark_unpaid":
        doc.status, doc.paid_at = "issued", None
    return doc
