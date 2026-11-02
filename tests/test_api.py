# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
COMPANY = {"name": "Ma Société", "siren": "123456789", "address_line1": "1 rue de la Paix",
           "postal_code": "57000", "city": "Metz"}


def make_client(c, **kw):
    data = {"name": "Client SARL", "siren": "987654321", "address_line1": "2 rue X", "postal_code": "57070",
            "city": "Metz", **kw}
    r = c.post("/api/clients", json=data)
    assert r.status_code == 201, r.text
    return r.json()


LINES = [
    {"kind": "section", "label": "Lot 1 — Maçonnerie"},
    {"label": "Mur parpaing", "quantity": "12.5", "unit": "m²", "unit_price": "45", "vat_rate": "10"},
    {"label": "Main d'œuvre", "quantity": "8", "unit": "h", "unit_price": "40", "vat_rate": "20"},
]


def test_auth_required(tmp_path):
    from fastapi.testclient import TestClient
    from sandik.app import create_app
    from sandik.config import load_settings
    with TestClient(create_app(load_settings(data_dir=tmp_path, auth=True))) as anon:
        assert anon.get("/api/clients").status_code == 401
        assert anon.get("/api/auth/status").json()["needs_setup"] is True
        assert anon.get("/api/edition").json()["name"] == "sandik"


def test_full_flow(client):
    cl = make_client(client)
    q = client.post("/api/documents", json={"type": "quote", "client_id": cl["id"], "title": "Extension",
                                            "lines": LINES}).json()
    assert q["number"].startswith("DEV-")
    assert q["total_ht"] == "882.50"  # 562.50 + 320
    assert q["total_vat"] == "120.25"  # 56.25 + 64
    assert "accept" in q["actions"]

    q = client.post(f"/api/documents/{q['id']}/actions/accept").json()
    inv = client.post(f"/api/documents/{q['id']}/actions/to_invoice").json()
    assert inv["type"] == "invoice" and inv["number"] is None and inv["source_id"] == q["id"]

    # émission impossible tant que l'entreprise n'est pas renseignée
    r = client.post(f"/api/documents/{inv['id']}/actions/issue")
    assert r.status_code == 422
    assert "company.siren" in r.json()["detail"]["details"]

    client.put("/api/settings/company", json=COMPANY)
    # un brouillon supprimé ne consomme pas de numéro
    draft = client.post("/api/documents", json={"type": "invoice", "client_id": cl["id"], "lines": LINES}).json()
    assert client.delete(f"/api/documents/{draft['id']}").json() == {"deleted": True}

    inv = client.post(f"/api/documents/{inv['id']}/actions/issue").json()
    assert inv["status"] == "issued"
    assert inv["number"].endswith("-0001")
    assert len(inv["integrity_hash"]) == 64
    assert inv["issuer"]["siren"] == "123456789"

    # une facture émise est figée
    assert client.put(f"/api/documents/{inv['id']}", json={"title": "x"}).status_code == 422
    assert client.delete(f"/api/documents/{inv['id']}").status_code == 409

    av = client.post(f"/api/documents/{inv['id']}/actions/credit_note").json()
    av = client.post(f"/api/documents/{av['id']}/actions/issue").json()
    assert av["number"].startswith("AV-") and av["status"] == "issued"

    dash = client.get("/api/dashboard").json()
    assert dash["revenue_ht"] == "0.00"


def test_vat_franchise(client):
    client.put("/api/settings/vat", json={"regime": "franchise"})
    cl = make_client(client)
    d = client.post("/api/documents", json={"type": "quote", "client_id": cl["id"], "lines": LINES}).json()
    assert d["total_vat"] == "0.00"
    assert "293 B" in d["vat_exemption_text"]


def test_numbering_validation(client):
    r = client.put("/api/settings/numbering", json={"invoice": "FACT-{N:5}"})
    assert r.status_code == 422
    r = client.put("/api/settings/numbering", json={"invoice": "FACT-{YYYY}-{N:5}"})
    assert r.status_code == 200


def test_client_siren_required_for_business(client):
    client.put("/api/settings/company", json=COMPANY)
    cl = make_client(client, siren="")
    inv = client.post("/api/documents", json={"type": "invoice", "client_id": cl["id"], "lines": LINES}).json()
    r = client.post(f"/api/documents/{inv['id']}/actions/issue")
    assert r.status_code == 422
    person = make_client(client, kind="individual", siren="", name="M. Dupont")
    inv2 = client.post("/api/documents", json={"type": "invoice", "client_id": person["id"], "lines": LINES}).json()
    assert client.post(f"/api/documents/{inv2['id']}/actions/issue").status_code == 200
