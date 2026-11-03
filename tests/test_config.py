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


def test_network_settings(tmp_path):
    from sandik.services.network import validate_local_name, validate_public_url

    assert validate_local_name("sandik") and validate_local_name("bureau-2")
    assert not validate_local_name("Sandik!") and not validate_local_name("-x")
    assert validate_public_url("https://factures.exemple.fr") and validate_public_url("http://sandik.com:5761")
    assert not validate_public_url("ftp://x") and not validate_public_url("pas une adresse")

    settings = load_settings(data_dir=tmp_path, auth=False, port=5761, host="0.0.0.0")
    with TestClient(create_app(settings)) as c:
        n = c.get("/api/system/network").json()
        assert n["port"] == 5761 and n["local_url"] == "http://sandik.local:5761" and n["mdns"] is False
        r = c.put("/api/system/network", json={"public_url": "https://sandik.com/", "local_name": "factures"})
        assert r.status_code == 200, r.text
        assert r.json()["public_url"] == "https://sandik.com" and r.json()["local_url"] == "http://factures.local:5761"
        assert c.put("/api/system/network", json={"public_url": "n'importe quoi"}).status_code == 422
        assert c.put("/api/system/network", json={"local_name": "Nom Invalide"}).status_code == 422


def test_public_url_from_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDIK_PUBLIC_URL", "https://factures.exemple.fr/")
    with TestClient(create_app(load_settings(data_dir=tmp_path, auth=False))) as c:
        n = c.get("/api/system/network").json()
        assert n["public_url"] == "https://factures.exemple.fr" and n["public_url_locked"] is True


def test_dyndns_settings(tmp_path):
    from sandik.services.network import dyndns_url

    assert dyndns_url({"dyndns_enabled": False}) is None
    assert dyndns_url({"dyndns_enabled": True, "dyndns_provider": "duckdns", "duckdns_subdomain": "monentreprise",
                       "duckdns_token": "abc"}) == "https://www.duckdns.org/update?domains=monentreprise&token=abc&ip="
    assert dyndns_url({"dyndns_enabled": True, "dyndns_provider": "custom", "dyndns_url": "https://u:p@update.dedyn.io/"})
    with TestClient(create_app(load_settings(data_dir=tmp_path, auth=False))) as c:
        r = c.put("/api/system/network", json={"duckdns_subdomain": "monentreprise.duckdns.org", "duckdns_token": "secret"})
        n = r.json()
        assert n["duckdns_subdomain"] == "monentreprise" and n["duckdns_token"] == "••••••••"  # jeton masqué
        # le masque renvoyé par le formulaire ne remplace pas le vrai jeton
        c.put("/api/system/network", json={"duckdns_token": "••••••••"})
        from sandik.services.settings_store import get_setting
        app = c.app
        with app.state.sessionmaker() as db:
            assert get_setting(db, app.state.edition, "network")["duckdns_token"] == "secret"
