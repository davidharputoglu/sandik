# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Éditions : nom, identité visuelle, modules et réglages par défaut d'un produit.

sandik (version libre) et BatiPilot (version privée) sont deux éditions du même cœur.
Une édition est un dossier contenant un fichier ``edition.toml`` et ses visuels.
Les éditions installées se déclarent via le point d'entrée ``sandik.editions``.
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

SANDIK_DIR = Path(__file__).parent / "sandik"

DEFAULTS: dict[str, Any] = {
    "theme": {
        "primary": "#0fa39c",
        "primary_strong": "#0b7f7a",
        "primary_soft": "#e2f6f5",
        "ink": "#2f363f",
        "muted": "#6b7480",
        "radius": "10px",
        "mode": "auto",
    },
    "modules": {"enabled": "*", "disabled": []},
    "defaults": {
        "currency": "EUR",
        "locale": "fr-FR",
        "quote_validity_days": 30,
        "payment_terms_days": 30,
    },
    "i18n": {"languages": ["fr", "en"], "default": "fr"},
    "numbering": {
        "quote": "DEV-{YYYY}-{N:4}",
        "invoice": "FAC-{YYYY}-{N:4}",
        "credit_note": "AV-{YYYY}-{N:4}",
        "reset": "yearly",
    },
}


@dataclass
class Edition:
    id: str
    name: str
    tagline: str
    license: str
    directory: Path
    about: dict[str, str]
    theme: dict[str, Any]
    assets: dict[str, str]
    modules: dict[str, Any]
    defaults: dict[str, Any]
    numbering: dict[str, Any]
    i18n: dict[str, Any]
    themes: list[dict[str, Any]]
    extra: dict[str, Any] = field(default_factory=dict)

    def asset_path(self, name: str) -> Path | None:
        filename = self.assets.get(name)
        if not filename:
            return None
        path = (self.directory / filename).resolve()
        if self.directory.resolve() not in path.parents or not path.is_file():
            return None
        return path

    def module_allowed(self, module_id: str) -> bool:
        if module_id in self.modules.get("disabled", []):
            return False
        enabled = self.modules.get("enabled", "*")
        return enabled == "*" or module_id in enabled


def installed_editions() -> dict[str, Path]:
    found = {"sandik": SANDIK_DIR}
    for ep in entry_points(group="sandik.editions"):
        try:
            found[ep.name] = Path(ep.load())
        except Exception:  # pragma: no cover - une édition cassée ne doit pas bloquer les autres
            continue
    return found


def load_edition(name_or_path: str) -> Edition:
    candidate = Path(name_or_path)
    if candidate.is_dir() and (candidate / "edition.toml").is_file():
        directory = candidate
    else:
        editions = installed_editions()
        if name_or_path not in editions:
            known = ", ".join(sorted(editions))
            raise RuntimeError(f"Édition inconnue : {name_or_path!r}. Éditions installées : {known}")
        directory = editions[name_or_path]

    raw = tomllib.loads((directory / "edition.toml").read_text(encoding="utf-8"))
    meta = raw.get("edition", {})

    def merged(section: str) -> dict[str, Any]:
        value = copy.deepcopy(DEFAULTS.get(section, {}))
        value.update(raw.get(section, {}))
        return value

    known_sections = {"edition", "theme", "assets", "modules", "defaults", "numbering", "i18n", "themes"}
    themes = list(raw.get("themes", []))
    if not themes:  # édition sans thèmes : un thème clair construit à partir de [theme]
        themes = [{"id": "default", "name": meta.get("name", "Défaut"), "mode": "light", **merged("theme")}]
    return Edition(
        id=meta.get("id", directory.name),
        name=meta.get("name", directory.name),
        tagline=meta.get("tagline", ""),
        license=meta.get("license", ""),
        directory=directory,
        about={k: str(meta.get(k, "")) for k in ("author", "contact", "credits", "copyright", "source_url")},
        theme=merged("theme"),
        assets=dict(raw.get("assets", {})),
        modules=merged("modules"),
        defaults=merged("defaults"),
        numbering=merged("numbering"),
        i18n=merged("i18n"),
        themes=themes,
        extra={k: v for k, v in raw.items() if k not in known_sections},
    )
