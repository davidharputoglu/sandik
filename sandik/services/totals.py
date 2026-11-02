# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Calcul des montants. Règle : TVA calculée par taux sur le total HT de chaque taux."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Protocol

CENT = Decimal("0.01")
ZERO = Decimal("0")


class LineLike(Protocol):
    kind: str
    quantity: Decimal
    unit_price: Decimal
    discount_percent: Decimal
    vat_rate: Decimal
    total_ht: Decimal


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(quantity: Decimal, unit_price: Decimal, discount_percent: Decimal = ZERO) -> Decimal:
    gross = Decimal(quantity) * Decimal(unit_price)
    return money(gross * (Decimal(100) - Decimal(discount_percent)) / Decimal(100))


def compute_totals(lines: Iterable[LineLike]) -> dict:
    """Met à jour ``total_ht`` de chaque ligne et renvoie les totaux du document."""
    bases: dict[Decimal, Decimal] = {}
    for line in lines:
        if line.kind != "item":
            line.total_ht = ZERO
            continue
        line.total_ht = line_total(line.quantity, line.unit_price, line.discount_percent)
        rate = Decimal(line.vat_rate).normalize()
        bases[rate] = bases.get(rate, ZERO) + line.total_ht
    breakdown = []
    total_ht = total_vat = ZERO
    for rate in sorted(bases, reverse=True):
        base = money(bases[rate])
        vat = money(base * rate / Decimal(100))
        breakdown.append({"rate": format(rate, "f"), "base": str(base), "vat": str(vat)})
        total_ht += base
        total_vat += vat
    return {
        "total_ht": money(total_ht),
        "total_vat": money(total_vat),
        "total_ttc": money(total_ht + total_vat),
        "vat_breakdown": breakdown,
    }
