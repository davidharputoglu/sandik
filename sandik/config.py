# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Configuration lue depuis les variables d'environnement (ou la ligne de commande)."""

from __future__ import annotations

import configparser
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "oui", "on"}


@dataclass(frozen=True)
class Settings:
    edition: str
    data_dir: Path
    database_url: str
    auth: bool
    desktop: bool
    cookie_secure: bool
    language: str | None = None
    config_file: Path | None = None


def config_path(folder_name: str) -> Path:
    """Fichier de configuration de l'utilisateur (écrit par l'assistant de premier lancement)."""
    return Path(user_config_dir(folder_name, appauthor=False)) / "config.ini"


def read_config(folder_name: str) -> dict[str, str]:
    """Réglages d'installation : fichier utilisateur, puis install.ini posé par l'installateur."""
    values: dict[str, str] = {}
    files = []
    if getattr(sys, "frozen", False):  # application installée (PyInstaller)
        files.append(Path(sys.executable).parent / "install.ini")
    files.append(config_path(folder_name))
    for file in files:  # le dernier lu l'emporte : l'utilisateur prime sur l'installateur
        if file.is_file():
            parser = configparser.ConfigParser()
            parser.read(file, encoding="utf-8")
            if parser.has_section("app"):
                values.update({k: v for k, v in parser.items("app") if v})
    return values


def write_config(folder_name: str, **values: str) -> Path:
    path = config_path(folder_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser()
    if path.is_file():
        parser.read(path, encoding="utf-8")
    if not parser.has_section("app"):
        parser.add_section("app")
    for key, value in values.items():
        parser.set("app", key, value)
    with path.open("w", encoding="utf-8") as fh:
        parser.write(fh)
    return path


def load_settings(
    *,
    edition: str | None = None,
    data_dir: str | Path | None = None,
    database_url: str | None = None,
    auth: bool | None = None,
    desktop: bool = False,
) -> Settings:
    env = os.environ
    edition = edition or env.get("SANDIK_EDITION") or "sandik"
    # Chaque édition a son propre dossier de données : sandik et BatiPilot ne se mélangent jamais.
    folder_name = Path(edition).name if Path(edition).is_dir() else edition
    cfg = read_config(folder_name)
    data = Path(data_dir or env.get("SANDIK_DATA_DIR") or cfg.get("data_dir") or user_data_dir(folder_name, appauthor=False))
    data.mkdir(parents=True, exist_ok=True)
    db_url = (
        database_url
        or env.get("SANDIK_DATABASE_URL")
        or f"sqlite:///{(data / (folder_name + '.db')).as_posix()}"
    )
    if auth is None:
        # Bureau (un seul poste) : pas de connexion par défaut. Serveur / Docker : connexion obligatoire.
        auth = _bool(env.get("SANDIK_AUTH"), default=not desktop)
    return Settings(
        edition=edition,
        data_dir=data,
        database_url=db_url,
        auth=auth,
        desktop=desktop,
        cookie_secure=_bool(env.get("SANDIK_COOKIE_SECURE"), default=False),
        language=env.get("SANDIK_LANG") or cfg.get("language") or None,
        config_file=config_path(folder_name),
    )
