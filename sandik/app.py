# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Création de l'application."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import auth, documents, edition, extensions, records, system
from .config import Settings, load_settings
from .db import Base, make_engine, make_sessionmaker
from .editions import load_edition
from .modules import ModuleError, load_modules
from .services.documents import BusinessError
from .services.settings_store import get_setting

STATIC_DIR = Path(__file__).parent / "static"
log = logging.getLogger("sandik")

NOT_BUILT = """<!doctype html><meta charset="utf-8"><title>{name}</title>
<body style="font-family:system-ui;max-width:640px;margin:4rem auto;line-height:1.5">
<h1>{name}</h1><p>Le serveur fonctionne, mais l'interface n'est pas encore compilée.</p>
<p>Dans le dossier <code>frontend</code> : <code>npm install</code> puis <code>npm run build</code>.</p>
<p>Documentation de l'API : <a href="/api/docs">/api/docs</a></p></body>"""


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    ed = load_edition(settings.edition)
    engine = make_engine(settings.database_url)
    Base.metadata.create_all(engine)

    app = FastAPI(
        title=ed.name, version=__version__,
        docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json",
    )
    app.state.settings = settings
    app.state.edition = ed
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)

    app.include_router(auth.router)
    app.include_router(edition.public)
    app.include_router(edition.router)
    app.include_router(records.router)
    app.include_router(documents.router)
    app.include_router(extensions.router)
    app.include_router(system.router)

    @app.get("/api/health", include_in_schema=False)
    def health():
        return {"status": "ok", "edition": ed.id, "version": __version__}

    @app.exception_handler(BusinessError)
    async def business_error(_: Request, exc: BusinessError):
        return JSONResponse(status_code=422, content={"detail": {"code": exc.code, "message": exc.message,
                                                                     "details": exc.details, "params": exc.params}})

    @app.exception_handler(ModuleError)
    async def module_error(_: Request, exc: ModuleError):
        return JSONResponse(status_code=422, content={"detail": {"code": "module", "message": str(exc), "details": [], "params": {}}})

    # Modules (après le cœur, avant l'interface qui capte toutes les autres adresses)
    modules_dir = settings.data_dir / "modules"
    modules_dir.mkdir(parents=True, exist_ok=True)
    with app.state.sessionmaker() as db:
        disabled = get_setting(db, ed, "modules").get("disabled", [])
    app.state.modules_dir = modules_dir
    app.state.modules = load_modules(app, ed, modules_dir, disabled)

    index = STATIC_DIR / "index.html"

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    def spa():
        if not index.is_file():
            return HTMLResponse(NOT_BUILT.format(name=ed.name))
        html = index.read_text(encoding="utf-8")
        html = html.replace("__APP_NAME__", ed.name).replace("__THEME_COLOR__", ed.theme.get("primary", "#0fa39c"))
        return HTMLResponse(html, headers={"Cache-Control": "no-cache"})

    if (STATIC_DIR / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    log.info("%s %s prêt (édition %s, base %s)", ed.name, __version__, ed.id, engine.url.get_backend_name())
    return app
