# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
import pytest
from fastapi.testclient import TestClient

from sandik.app import create_app
from sandik.config import load_settings


@pytest.fixture()
def client(tmp_path):
    settings = load_settings(data_dir=tmp_path, auth=True)
    with TestClient(create_app(settings)) as c:
        r = c.post("/api/auth/setup", json={"name": "Admin", "email": "admin@exemple.fr", "password": "motdepasse1"})
        assert r.status_code == 200, r.text
        yield c
