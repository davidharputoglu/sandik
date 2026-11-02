# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
from fastapi.testclient import TestClient

from sandik import config
from sandik.app import create_app
from sandik.config import load_settings


def test_config_file_sets_language_and_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "user_config_dir", lambda name, appauthor=False: str(tmp_path / "cfg"))
    monkeypatch.delenv("SANDIK_DATA_DIR", raising=False)
    monkeypatch.delenv("SANDIK_LANG", raising=False)
    config.write_config("sandik", language="tr", data_dir=str(tmp_path / "donnees"))
    s = load_settings()
    assert s.language == "tr"
    assert s.data_dir == tmp_path / "donnees"


def test_desktop_location_change_copies_database(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "user_config_dir", lambda name, appauthor=False: str(tmp_path / "cfg"))
    settings = load_settings(data_dir=tmp_path / "a", desktop=True)
    with TestClient(create_app(settings)) as c:
        c.put("/api/settings/company", json={"name": "Société test"})
        assert c.get("/api/system/location").json()["can_change"] is True
        r = c.put("/api/system/location", json={"data_dir": str(tmp_path / "b"), "language": "en"})
        assert r.json()["restart_required"] is True
    assert (tmp_path / "b" / "sandik.db").is_file()
    s2 = load_settings(desktop=True)
    assert s2.data_dir == tmp_path / "b" and s2.language == "en"
    with TestClient(create_app(s2)) as c:  # la base copiée contient les réglages
        assert c.get("/api/settings").json()["company"]["name"] == "Société test"
