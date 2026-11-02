# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Clients et catalogue d'articles."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Article, Client, Document
from ..schemas import ArticleIn, ClientIn, dump_article, dump_client
from .auth import require_user

router = APIRouter(prefix="/api", tags=["clients", "articles"], dependencies=[Depends(require_user)])


def _like(q: str) -> str:
    return f"%{q.strip().lower()}%"


# ---------------------------------------------------------------- clients
@router.get("/clients")
def list_clients(q: str = "", archived: bool = False, db: Session = Depends(get_db)):
    stmt = select(Client).where(Client.archived == archived).order_by(func.lower(Client.name))
    if q:
        stmt = stmt.where(or_(func.lower(Client.name).like(_like(q)), func.lower(Client.city).like(_like(q)),
                              func.lower(Client.email).like(_like(q)), Client.siren.like(_like(q))))
    return [dump_client(c) for c in db.scalars(stmt)]


@router.post("/clients", status_code=201)
def create_client(data: ClientIn, request: Request, db: Session = Depends(get_db)):
    client = Client(**data.model_dump())
    db.add(client)
    db.flush()
    request.app.state.modules.emit("client.saved", db=db, client=client)
    db.commit()
    return dump_client(client)


@router.get("/clients/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable.")
    return dump_client(client)


@router.put("/clients/{client_id}")
def update_client(client_id: int, data: ClientIn, request: Request, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable.")
    for k, v in data.model_dump().items():
        setattr(client, k, v)
    request.app.state.modules.emit("client.saved", db=db, client=client)
    db.commit()
    return dump_client(client)


@router.delete("/clients/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404)
    used = db.scalar(select(func.count(Document.id)).where(Document.client_id == client_id))
    if used:
        client.archived = True  # un client avec des documents n'est jamais supprimé, il est archivé
        db.commit()
        return {"archived": True}
    db.delete(client)
    db.commit()
    return {"deleted": True}


# ---------------------------------------------------------------- articles
@router.get("/articles")
def list_articles(q: str = "", archived: bool = False, db: Session = Depends(get_db)):
    stmt = select(Article).where(Article.archived == archived).order_by(func.lower(Article.label))
    if q:
        stmt = stmt.where(or_(func.lower(Article.label).like(_like(q)), func.lower(Article.reference).like(_like(q))))
    return [dump_article(a) for a in db.scalars(stmt)]


@router.post("/articles", status_code=201)
def create_article(data: ArticleIn, db: Session = Depends(get_db)):
    article = Article(**data.model_dump())
    db.add(article)
    db.commit()
    return dump_article(article)


@router.put("/articles/{article_id}")
def update_article(article_id: int, data: ArticleIn, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable.")
    for k, v in data.model_dump().items():
        setattr(article, k, v)
    db.commit()
    return dump_article(article)


@router.delete("/articles/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if article:
        db.delete(article)
        db.commit()
    return {"deleted": True}
