# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from sandik.services.numbering import render, validate_pattern
from sandik.services.totals import compute_totals, line_total


def test_render_pattern():
    assert render("FAC-{YYYY}-{N:4}", 7, date(2026, 11, 2)) == "FAC-2026-0007"
    assert render("F{YY}{MM}-{N}", 12, date(2026, 3, 1)) == "F2603-12"


def test_validate_pattern():
    assert validate_pattern("FAC-{YYYY}-{N:4}", "yearly") == []
    assert validate_pattern("FAC-{N:4}", "yearly")  # année manquante
    assert validate_pattern("FAC-{YYYY}", "never")  # compteur manquant


def test_line_total_and_discount():
    assert line_total(Decimal("3"), Decimal("33.333"), Decimal("0")) == Decimal("100.00")
    assert line_total(Decimal("2"), Decimal("50"), Decimal("10")) == Decimal("90.00")


def test_vat_by_rate():
    L = lambda q, p, r, kind="item": SimpleNamespace(kind=kind, quantity=Decimal(q), unit_price=Decimal(p),
                                                    discount_percent=Decimal("0"), vat_rate=Decimal(r), total_ht=None)
    t = compute_totals([L("1", "100", "20"), L("2", "50", "10"), L("1", "0", "20", kind="section")])
    assert t["total_ht"] == Decimal("200.00")
    assert t["total_vat"] == Decimal("30.00")
    assert t["total_ttc"] == Decimal("230.00")
    assert [b["rate"] for b in t["vat_breakdown"]] == ["20", "10"]
