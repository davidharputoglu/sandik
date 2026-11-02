# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Base de données : SQLite (bureau) ou PostgreSQL (serveur / Docker)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Iterator

from fastapi import Request
from sqlalchemy import Numeric, String, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class Dec(TypeDecorator):
    """Décimal exact : NUMERIC sous PostgreSQL, texte sous SQLite (jamais de flottant)."""

    impl = String
    cache_ok = True

    def __init__(self, scale: int = 2):
        super().__init__()
        self.scale = scale
        self._q = Decimal(1).scaleb(-scale)

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(40))
        return dialect.type_descriptor(Numeric(18, self.scale))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        d = Decimal(str(value)).quantize(self._q, rounding=ROUND_HALF_UP)
        return str(d) if dialect.name == "sqlite" else d

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Decimal(str(value)).quantize(self._q, rounding=ROUND_HALF_UP)


def make_engine(url: str) -> Engine:
    kwargs: dict = {"future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _record):  # pragma: no cover - simple configuration
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA journal_mode=WAL")
            cur.close()

    return engine


def make_sessionmaker(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db(request: Request) -> Iterator[Session]:
    db = request.app.state.sessionmaker()
    try:
        yield db
    finally:
        db.close()
