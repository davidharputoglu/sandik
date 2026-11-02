# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Schémas d'entrée (validation) et fonctions de sortie (JSON)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import Article, Client, CustomField, Document, DocumentLine
from .services.documents import LABELS, allowed_actions, is_editable


class In(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


# ---------------------------------------------------------------- clients / articles
class ClientIn(In):
    kind: Literal["company", "individual"] = "company"
    name: str = Field(min_length=1, max_length=255)
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    siren: str = ""
    vat_number: str = ""
    address_line1: str = ""
    address_line2: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = Field(default="FR", max_length=2)
    notes: str = ""
    extra: dict[str, Any] = Field(default_factory=dict)
    archived: bool = False

    @field_validator("siren")
    @classmethod
    def _siren(cls, v: str) -> str:
        v = v.replace(" ", "")
        if v and (not v.isdigit() or len(v) != 9):
            raise ValueError("Le SIREN doit comporter 9 chiffres.")
        return v

    @field_validator("country")
    @classmethod
    def _country(cls, v: str) -> str:
        return (v or "FR").upper()


class ArticleIn(In):
    reference: str = ""
    label: str = Field(min_length=1, max_length=255)
    description: str = ""
    unit: str = "u"
    unit_price: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("20")
    nature: Literal["service", "goods"] = "service"
    extra: dict[str, Any] = Field(default_factory=dict)
    archived: bool = False


# ---------------------------------------------------------------- documents
class LineIn(In):
    kind: Literal["item", "section", "text"] = "item"
    article_id: int | None = None
    reference: str = ""
    label: str = ""
    description: str = ""
    quantity: Decimal = Decimal("1")
    unit: str = ""
    unit_price: Decimal = Decimal("0")
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    vat_rate: Decimal = Field(default=Decimal("20"), ge=0, le=100)


class DocumentIn(In):
    type: Literal["quote", "invoice", "credit_note"] | None = None
    client_id: int | None = None
    title: str | None = None
    issue_date: date | None = None
    valid_until: date | None = None
    due_date: date | None = None
    operation_nature: Literal["services", "goods", "mixed"] | None = None
    vat_on_debits: bool | None = None
    vat_exemption_text: str | None = None
    delivery_address: str | None = None
    intro: str | None = None
    notes: str | None = None
    terms: str | None = None
    extra: dict[str, Any] | None = None
    lines: list[LineIn] | None = None


class ActionIn(In):
    issue_date: date | None = None
    paid_at: date | None = None


class CustomFieldIn(In):
    entity: Literal["client", "article", "document"]
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    label: str = Field(min_length=1, max_length=255)
    type: Literal["text", "textarea", "number", "date", "boolean", "select"] = "text"
    options: list[str] = Field(default_factory=list)
    required: bool = False
    show_on_pdf: bool = False
    position: int = 0


class SetupIn(In):
    name: str = Field(min_length=1)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)


class LoginIn(In):
    email: str
    password: str


# ---------------------------------------------------------------- sorties
def s(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def price(value: Decimal | None) -> str | None:
    """Prix : 2 décimales, ou jusqu'à 4 si nécessaire (180.0000 → 180.00 ; 0.1234 → 0.1234)."""
    if value is None:
        return None
    d = value.normalize()
    return format(d if d.as_tuple().exponent < -2 else value.quantize(Decimal("0.01")), "f")


def dump_client(c: Client) -> dict[str, Any]:
    return {
        "id": c.id, "kind": c.kind, "name": c.name, "contact_name": c.contact_name, "email": c.email,
        "phone": c.phone, "siren": c.siren, "vat_number": c.vat_number, "address_line1": c.address_line1,
        "address_line2": c.address_line2, "postal_code": c.postal_code, "city": c.city, "country": c.country,
        "notes": c.notes, "extra": c.extra or {}, "archived": c.archived,
    }


def dump_article(a: Article) -> dict[str, Any]:
    return {
        "id": a.id, "reference": a.reference, "label": a.label, "description": a.description, "unit": a.unit,
        "unit_price": price(a.unit_price), "vat_rate": s(a.vat_rate.normalize()), "nature": a.nature,
        "extra": a.extra or {}, "archived": a.archived,
    }


def dump_line(line: DocumentLine) -> dict[str, Any]:
    return {
        "id": line.id, "position": line.position, "kind": line.kind, "article_id": line.article_id,
        "reference": line.reference, "label": line.label, "description": line.description,
        "quantity": s(line.quantity.normalize()), "unit": line.unit, "unit_price": price(line.unit_price),
        "discount_percent": s(line.discount_percent.normalize()), "vat_rate": s(line.vat_rate.normalize()),
        "total_ht": s(line.total_ht),
    }


def dump_document(d: Document, full: bool = True) -> dict[str, Any]:
    out = {
        "id": d.id, "type": d.type, "type_label": LABELS[d.type], "status": d.status, "number": d.number,
        "client_id": d.client_id, "client_name": (d.client_snapshot or {}).get("name") or d.client.name,
        "title": d.title, "issue_date": d.issue_date, "valid_until": d.valid_until, "due_date": d.due_date,
        "paid_at": d.paid_at, "total_ht": s(d.total_ht), "total_vat": s(d.total_vat), "total_ttc": s(d.total_ttc),
        "source_id": d.source_id, "editable": is_editable(d), "actions": allowed_actions(d),
        "created_at": d.created_at, "updated_at": d.updated_at,
    }
    if full:
        out.update({
            "operation_nature": d.operation_nature, "vat_on_debits": d.vat_on_debits,
            "vat_exemption_text": d.vat_exemption_text, "delivery_address": d.delivery_address,
            "intro": d.intro, "notes": d.notes, "terms": d.terms, "vat_breakdown": d.vat_breakdown,
            "client": d.client_snapshot or dump_client(d.client), "issuer": d.issuer_snapshot,
            "integrity_hash": d.integrity_hash, "extra": d.extra or {},
            "lines": [dump_line(line) for line in d.lines],
        })
    return out


def dump_field(f: CustomField) -> dict[str, Any]:
    return {
        "id": f.id, "entity": f.entity, "key": f.key, "label": f.label, "type": f.type, "options": f.options or [],
        "required": f.required, "show_on_pdf": f.show_on_pdf, "position": f.position, "source": "user",
    }
