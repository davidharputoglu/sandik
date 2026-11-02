# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Modèle de données."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, Dec


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Setting(Base):
    """Réglages clé → JSON (entreprise, numérotation, apparence, ...)."""

    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON, default=dict)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="user")  # admin | user
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    user: Mapped[User] = relationship()


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), default="company")  # company | individual
    name: Mapped[str] = mapped_column(String(255))
    contact_name: Mapped[str] = mapped_column(String(255), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    siren: Mapped[str] = mapped_column(String(32), default="")
    vat_number: Mapped[str] = mapped_column(String(32), default="")
    address_line1: Mapped[str] = mapped_column(String(255), default="")
    address_line2: Mapped[str] = mapped_column(String(255), default="")
    postal_code: Mapped[str] = mapped_column(String(16), default="")
    city: Mapped[str] = mapped_column(String(128), default="")
    country: Mapped[str] = mapped_column(String(2), default="FR")
    notes: Mapped[str] = mapped_column(Text, default="")
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Article(Base):
    """Catalogue : prestations, fournitures, ouvrages."""

    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(64), default="")
    label: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    unit: Mapped[str] = mapped_column(String(16), default="u")
    unit_price: Mapped[Decimal] = mapped_column(Dec(4), default=Decimal("0"))
    vat_rate: Mapped[Decimal] = mapped_column(Dec(2), default=Decimal("20"))
    nature: Mapped[str] = mapped_column(String(16), default="service")  # service | goods
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Document(Base):
    """Devis, facture ou avoir."""

    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("type", "number", name="uq_document_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(16), index=True)  # quote | invoice | credit_note
    status: Mapped[str] = mapped_column(String(16), default="draft", index=True)
    number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    title: Mapped[str] = mapped_column(String(255), default="")
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    operation_nature: Mapped[str] = mapped_column(String(16), default="services")  # services | goods | mixed
    vat_on_debits: Mapped[bool] = mapped_column(Boolean, default=False)
    vat_exemption_text: Mapped[str] = mapped_column(String(255), default="")
    delivery_address: Mapped[str] = mapped_column(Text, default="")
    intro: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    terms: Mapped[str] = mapped_column(Text, default="")
    total_ht: Mapped[Decimal] = mapped_column(Dec(2), default=Decimal("0"))
    total_vat: Mapped[Decimal] = mapped_column(Dec(2), default=Decimal("0"))
    total_ttc: Mapped[Decimal] = mapped_column(Dec(2), default=Decimal("0"))
    vat_breakdown: Mapped[list] = mapped_column(JSON, default=list)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    client_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    issuer_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    previous_hash: Mapped[str] = mapped_column(String(64), default="")
    integrity_hash: Mapped[str] = mapped_column(String(64), default="")
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    client: Mapped[Client] = relationship()
    lines: Mapped[list["DocumentLine"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentLine.position"
    )


class DocumentLine(Base):
    __tablename__ = "document_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    kind: Mapped[str] = mapped_column(String(16), default="item")  # item | section | text
    article_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id", ondelete="SET NULL"), nullable=True)
    reference: Mapped[str] = mapped_column(String(64), default="")
    label: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    quantity: Mapped[Decimal] = mapped_column(Dec(3), default=Decimal("1"))
    unit: Mapped[str] = mapped_column(String(16), default="")
    unit_price: Mapped[Decimal] = mapped_column(Dec(4), default=Decimal("0"))
    discount_percent: Mapped[Decimal] = mapped_column(Dec(2), default=Decimal("0"))
    vat_rate: Mapped[Decimal] = mapped_column(Dec(2), default=Decimal("20"))
    total_ht: Mapped[Decimal] = mapped_column(Dec(2), default=Decimal("0"))

    document: Mapped[Document] = relationship(back_populates="lines")


class NumberSequence(Base):
    """Compteur de numérotation : continu, sans trou, par type et par période."""

    __tablename__ = "number_sequences"
    __table_args__ = (UniqueConstraint("doc_type", "period", name="uq_sequence"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    doc_type: Mapped[str] = mapped_column(String(16))
    period: Mapped[str] = mapped_column(String(16))
    last_value: Mapped[int] = mapped_column(Integer, default=0)


class CustomField(Base):
    """Champ personnalisé ajouté par l'utilisateur sur les clients, articles ou documents."""

    __tablename__ = "custom_fields"
    __table_args__ = (UniqueConstraint("entity", "key", name="uq_custom_field"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    entity: Mapped[str] = mapped_column(String(16))  # client | article | document
    key: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(16), default="text")  # text | textarea | number | date | boolean | select
    options: Mapped[list] = mapped_column(JSON, default=list)
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    show_on_pdf: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
