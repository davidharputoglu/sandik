# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
import io
import zipfile

from fastapi.testclient import TestClient

from sandik.app import create_app
from sandik.config import load_settings

MANIFEST = """
[module]
id = "essai"
name = "Module d'essai"
version = "1.0.0"
entry = "module:Essai"
categories = ["services"]
"""
CODE = """
from fastapi import APIRouter
from sandik.modules import Module, ModuleError

class Essai(Module):
    def setup(self, ctx):
        router = APIRouter()
        @router.get("/ping")
        def ping():
            return {"pong": True}
        ctx.add_router(router)
        ctx.add_menu("Essai", "/modules/essai/")
        ctx.add_field("client", "code_essai", "Code d'essai")
        def bloquer(db, document):
            if document.title == "interdit":
                raise ModuleError("Bloqué par le module")
        ctx.on("document.before_issue", bloquer)
"""


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


def test_import_and_load(tmp_path):
    settings = load_settings(data_dir=tmp_path, auth=False)
    with TestClient(create_app(settings)) as c:
        r = c.post("/api/modules-admin/import", content=make_zip({"essai/module.toml": MANIFEST, "essai/module.py": CODE}))
        assert r.status_code == 200, r.text
        assert r.json()["restart_required"] is True
        mods = c.get("/api/modules-admin").json()["modules"]
        assert any(m["id"] == "essai" and m["reason"] == "restart" for m in mods)

    # au redémarrage, le module est chargé
    with TestClient(create_app(settings)) as c:
        ed = c.get("/api/edition").json()
        assert ed["modules"][0]["id"] == "essai"
        assert ed["modules"][0]["menu"][0]["label"] == "Essai"
        assert c.get("/api/modules/essai/ping").json() == {"pong": True}
        fields = c.get("/api/custom-fields?entity=client").json()
        assert any(f["key"] == "code_essai" for f in fields)
        # désactivation
        assert c.post("/api/modules-admin/essai/toggle").json()["disabled"] is True

    with TestClient(create_app(settings)) as c:
        assert c.get("/api/edition").json()["modules"] == []
        mods = c.get("/api/modules-admin").json()["modules"]
        assert mods[0]["reason"] == "disabled"


def test_reject_unsafe_archives(tmp_path):
    with TestClient(create_app(load_settings(data_dir=tmp_path, auth=False))) as c:
        bad = c.post("/api/modules-admin/import", content=b"pas un zip")
        assert bad.json()["detail"]["code"] == "module_import.invalid_zip"
        no_manifest = c.post("/api/modules-admin/import", content=make_zip({"a.py": "x"}))
        assert no_manifest.json()["detail"]["code"] == "module_import.no_manifest"
        evil = make_zip({"module.toml": MANIFEST, "../../evil.py": "x"})
        assert c.post("/api/modules-admin/import", content=evil).json()["detail"]["code"] == "module_import.unsafe_path"


def test_import_requires_admin(client):
    # utilisateur connecté = admin dans la fixture ; sans connexion → 401
    client.post("/api/auth/logout")
    assert client.post("/api/modules-admin/import", content=b"x").status_code == 401
