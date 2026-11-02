# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Système de modules.

Un module ajoute des fonctions sans toucher au cœur : routes d'API, entrées de menu,
pages, champs personnalisés et réactions aux événements (ex. avant l'émission d'une facture).

Un module se déclare dans le ``pyproject.toml`` de son paquet :

    [project.entry-points."sandik.modules"]
    mon_module = "mon_paquet.module:MonModule"

Un module peut aussi être *importé* depuis l'application (Paramètres → Modules) :
c'est une archive ``.zip`` contenant un fichier ``module.toml`` et son code Python.
Il est installé dans ``<dossier de données>/modules/<id>/`` et chargé au démarrage.

    module.toml
    -----------
    [module]
    id = "mon-module"            # lettres minuscules, chiffres, tirets
    name = "Mon module"
    version = "1.0.0"
    description = "..."
    entry = "module:MonModule"   # fichier module.py, classe MonModule
    editions = ["sandik"]        # facultatif : éditions autorisées
    categories = ["btp"]         # facultatif : métiers concernés

Les modules privés (BatiPilot) vivent dans leur propre dépôt et ne sont jamais publiés.
"""

from __future__ import annotations

import importlib.util
import io
import logging
import re
import shutil
import sys
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from .editions import Edition, tomllib

log = logging.getLogger("sandik.modules")

EVENTS = {
    "document.created",
    "document.updated",
    "document.before_issue",  # lever ModuleError pour bloquer l'émission
    "document.issued",
    "client.saved",
}


class ModuleError(Exception):
    """Erreur métier levée par un module : affichée telle quelle à l'utilisateur."""


@dataclass
class MenuEntry:
    module: str
    label: str
    path: str
    icon: str = "puzzle"


@dataclass
class FieldSpec:
    entity: str
    key: str
    label: str
    type: str = "text"
    options: list[str] = field(default_factory=list)
    required: bool = False
    show_on_pdf: bool = False
    source: str = ""


class Module:
    """Classe de base d'un module."""

    id: str = ""
    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    #: éditions où le module est autorisé (None = toutes). BatiPilot : ["batipilot"].
    editions: list[str] | None = None
    #: métiers concernés (btp, commerce, services, ...), pour le catalogue
    categories: list[str] = []
    #: "installed" (paquet Python) ou "imported" (archive importée depuis l'application)
    origin: str = "installed"

    def setup(self, ctx: "ModuleContext") -> None:  # pragma: no cover - à surcharger
        pass


class ModuleContext:
    def __init__(self, app: FastAPI, edition: Edition):
        self.app = app
        self.edition = edition
        self.menu: list[MenuEntry] = []
        self.fields: list[FieldSpec] = []
        self.hooks: dict[str, list[Callable[..., Any]]] = defaultdict(list)
        self.loaded: list[Module] = []
        self.skipped: list[dict[str, Any]] = []
        self._current: Module | None = None

    # --- API offerte aux modules -------------------------------------------------
    def add_router(self, router: APIRouter) -> None:
        """Routes servies sous /api/modules/<id>/..."""
        from .api.auth import require_user  # import tardif (évite les cycles)
        from fastapi import Depends

        self.app.include_router(
            router, prefix=f"/api/modules/{self._current.id}", dependencies=[Depends(require_user)]
        )

    def add_static(self, directory: str | Path) -> str:
        """Fichiers statiques (pages HTML, JS, images) servis sous /modules/<id>/."""
        url = f"/modules/{self._current.id}"
        self.app.mount(url, StaticFiles(directory=str(directory), html=True), name=f"module-{self._current.id}")
        return url

    def add_menu(self, label: str, path: str, icon: str = "puzzle") -> None:
        """Entrée de menu. ``path`` : page statique du module (ouverte dans l'application)."""
        self.menu.append(MenuEntry(module=self._current.id, label=label, path=path, icon=icon))

    def add_field(self, entity: str, key: str, label: str, type: str = "text", **kw: Any) -> None:
        self.fields.append(FieldSpec(entity=entity, key=key, label=label, type=type, source=self._current.id, **kw))

    def on(self, event: str, func: Callable[..., Any]) -> None:
        if event not in EVENTS:
            raise ValueError(f"Événement inconnu : {event}")
        self.hooks[event].append(func)

    # --- utilisé par le cœur -----------------------------------------------------
    def emit(self, event: str, **kwargs: Any) -> None:
        for func in self.hooks.get(event, []):
            func(**kwargs)

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "id": m.id,
                "name": m.name,
                "description": m.description,
                "version": m.version,
                "categories": list(m.categories),
                "origin": m.origin,
                "menu": [asdict(e) for e in self.menu if e.module == m.id],
            }
            for m in self.loaded
        ]


MODULE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,48}$")


def _imported_modules(modules_dir: Path) -> list[Module]:
    found: list[Module] = []
    if not modules_dir.is_dir():
        return found
    for folder in sorted(p for p in modules_dir.iterdir() if (p / "module.toml").is_file()):
        try:
            meta = tomllib.loads((folder / "module.toml").read_text(encoding="utf-8")).get("module", {})
            file_name, _, class_name = meta.get("entry", "module:Module").partition(":")
            spec = importlib.util.spec_from_file_location(
                f"sandik_ext_{folder.name.replace('-', '_')}", folder / f"{file_name}.py",
                submodule_search_locations=[str(folder)],
            )
            py = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = py
            spec.loader.exec_module(py)
            module: Module = getattr(py, class_name or "Module")()
            module.id = meta.get("id", folder.name)
            module.name = meta.get("name", module.name or module.id)
            module.version = meta.get("version", module.version)
            module.description = meta.get("description", module.description)
            module.editions = meta.get("editions", module.editions)
            module.categories = meta.get("categories", module.categories)
            module.origin = "imported"
            module.directory = folder
            found.append(module)
        except Exception:
            log.exception("Module importé %s impossible à charger", folder.name)
    return found


def _installed_modules() -> list[Module]:
    found: list[Module] = []
    for ep in sorted(entry_points(group="sandik.modules"), key=lambda e: e.name):
        try:
            target = ep.load()
            module: Module = target() if isinstance(target, type) else target
            module.id = module.id or ep.name
            found.append(module)
        except Exception:
            log.exception("Module %s impossible à charger", ep.name)
    return found


def install_archive(data: bytes, modules_dir: Path, edition: Edition) -> dict[str, Any]:
    """Installe une archive .zip de module. Renvoie ses informations. Lève ValueError si invalide."""
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ValueError("module_import.invalid_zip") from exc
    names = [n for n in archive.namelist() if not n.endswith("/")]
    manifest = next((n for n in names if n.rsplit("/", 1)[-1] == "module.toml" and n.count("/") <= 1), None)
    if manifest is None:
        raise ValueError("module_import.no_manifest")
    prefix = manifest[: -len("module.toml")]
    meta = tomllib.loads(archive.read(manifest).decode("utf-8")).get("module", {})
    module_id = str(meta.get("id", ""))
    if not MODULE_ID.match(module_id):
        raise ValueError("module_import.bad_id")
    editions = meta.get("editions")
    if editions and edition.id not in editions:
        raise ValueError("module_import.wrong_edition")
    target = modules_dir / module_id
    tmp = modules_dir / f".{module_id}.tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    for name in names:
        if not name.startswith(prefix):
            continue
        rel = Path(name[len(prefix):])
        if rel.is_absolute() or ".." in rel.parts:
            shutil.rmtree(tmp, ignore_errors=True)
            raise ValueError("module_import.unsafe_path")
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(archive.read(name))
    shutil.rmtree(target, ignore_errors=True)
    tmp.rename(target)
    return {"id": module_id, "name": meta.get("name", module_id), "version": meta.get("version", "")}


def load_modules(app: FastAPI, edition: Edition, modules_dir: Path | None = None,
                 disabled: list[str] | None = None) -> ModuleContext:
    ctx = ModuleContext(app, edition)
    disabled = set(disabled or [])
    imported = _imported_modules(modules_dir) if modules_dir else []
    imported_ids = {m.id for m in imported}
    candidates = [m for m in _installed_modules() if m.id not in imported_ids] + imported
    for module in candidates:
        reason = None
        if module.editions is not None and edition.id not in module.editions:
            continue  # module d'une autre édition : invisible
        if not edition.module_allowed(module.id):
            reason = "edition"
        elif module.id in disabled:
            reason = "disabled"
        if reason:
            ctx.skipped.append({"id": module.id, "name": module.name or module.id, "version": module.version,
                                "description": module.description, "origin": module.origin, "reason": reason})
            continue
        ctx._current = module
        try:
            module.setup(ctx)
            ctx.loaded.append(module)
            log.info("Module chargé : %s", module.id)
        except Exception:
            log.exception("Module %s : erreur au démarrage", module.id)
        finally:
            ctx._current = None
    return ctx
