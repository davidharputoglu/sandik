# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Numérotation légale : chronologique, continue, sans trou.

Le numéro d'une facture (ou d'un avoir) n'est attribué qu'au moment de son émission,
dans la même transaction : un brouillon supprimé ne crée donc jamais de trou.
Le format est personnalisable (préfixe, année, mois, nombre de chiffres).
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Document, NumberSequence

TOKEN = re.compile(r"\{(YYYY|YY|MM|N(?::(\d{1,2}))?)\}")


def validate_pattern(pattern: str, reset: str) -> list[str]:
    errors = []
    tokens = [m.group(1) for m in TOKEN.finditer(pattern)]
    if not any(t.startswith("N") for t in tokens):
        errors.append("Le format doit contenir le compteur {N} (ou {N:4} pour 4 chiffres).")
    has_year = "YYYY" in tokens or "YY" in tokens
    if reset in {"yearly", "monthly"} and not has_year:
        errors.append("Avec une remise à zéro annuelle ou mensuelle, le format doit contenir l'année {YYYY}.")
    if reset == "monthly" and "MM" not in tokens:
        errors.append("Avec une remise à zéro mensuelle, le format doit contenir le mois {MM}.")
    if len(pattern) > 40:
        errors.append("Format trop long (40 caractères maximum).")
    return errors


def period_for(reset: str, d: date) -> str:
    if reset == "yearly":
        return f"{d.year}"
    if reset == "monthly":
        return f"{d.year}-{d.month:02d}"
    return "all"


def render(pattern: str, n: int, d: date) -> str:
    def repl(m: re.Match) -> str:
        token = m.group(1)
        if token == "YYYY":
            return f"{d.year:04d}"
        if token == "YY":
            return f"{d.year % 100:02d}"
        if token == "MM":
            return f"{d.month:02d}"
        width = int(m.group(2) or 1)
        return f"{n:0{width}d}"

    return TOKEN.sub(repl, pattern)


def preview(pattern: str, d: date | None = None) -> str:
    return render(pattern, 1, d or date.today())


def next_number(db: Session, doc_type: str, numbering: dict, d: date) -> str:
    pattern = numbering[doc_type]
    reset = numbering.get("reset", "yearly")
    period = period_for(reset, d)
    seq = db.execute(
        select(NumberSequence)
        .where(NumberSequence.doc_type == doc_type, NumberSequence.period == period)
        .with_for_update()
    ).scalar_one_or_none()
    if seq is None:
        seq = NumberSequence(doc_type=doc_type, period=period, last_value=0)
        db.add(seq)
        db.flush()
    while True:
        seq.last_value += 1
        number = render(pattern, seq.last_value, d)
        taken = db.scalar(select(Document.id).where(Document.type == doc_type, Document.number == number))
        if not taken:  # sécurité si le format a été modifié en cours d'année
            return number
