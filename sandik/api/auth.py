# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
"""Connexion. Désactivée par défaut en mode bureau, obligatoire en mode serveur / Docker."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuthSession, User
from ..schemas import LoginIn, SetupIn

router = APIRouter(prefix="/api/auth", tags=["auth"])
SESSION_DAYS = 30


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, digest = stored.split("$")
        test = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(test.hex(), digest)
    except (ValueError, TypeError):
        return False


def _cookie(request: Request) -> str:
    return f"{request.app.state.edition.id}_session"


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request, db: Session) -> User | None:
    token = request.cookies.get(_cookie(request))
    if not token:
        return None
    sess = db.get(AuthSession, _token_hash(token))
    if not sess:
        return None
    expires = sess.expires_at if sess.expires_at.tzinfo else sess.expires_at.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc) or not sess.user.active:
        return None
    return sess.user


def require_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    if not request.app.state.settings.auth:
        return None
    user = current_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    return user


def _open_session(request: Request, response: Response, db: Session, user: User) -> None:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token_hash=_token_hash(token), user_id=user.id,
                       expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)))
    db.commit()
    response.set_cookie(
        _cookie(request), token, max_age=SESSION_DAYS * 86400, httponly=True, samesite="lax",
        # en HTTPS (directement ou derrière un relais web) le cookie n'est jamais envoyé en clair
        secure=request.app.state.settings.cookie_secure or request.url.scheme == "https",
    )


def _user_out(user: User | None) -> dict | None:
    return None if user is None else {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@router.get("/status")
def status(request: Request, db: Session = Depends(get_db)):
    enabled = request.app.state.settings.auth
    has_users = (db.scalar(select(func.count(User.id))) or 0) > 0
    return {
        "auth_enabled": enabled,
        "needs_setup": enabled and not has_users,
        "user": _user_out(current_user(request, db)) if enabled else None,
    }


@router.post("/setup")
def setup(data: SetupIn, request: Request, response: Response, db: Session = Depends(get_db)):
    if (db.scalar(select(func.count(User.id))) or 0) > 0:
        raise HTTPException(status_code=409, detail="Le compte administrateur existe déjà.")
    user = User(email=data.email.lower(), name=data.name, password_hash=hash_password(data.password), role="admin")
    db.add(user)
    db.commit()
    _open_session(request, response, db, user)
    return {"user": _user_out(user)}


@router.post("/login")
def login(data: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.strip().lower()))
    if not user or not user.active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Adresse e-mail ou mot de passe incorrect.")
    _open_session(request, response, db, user)
    return {"user": _user_out(user)}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(_cookie(request))
    if token:
        sess = db.get(AuthSession, _token_hash(token))
        if sess:
            db.delete(sess)
            db.commit()
    response.delete_cookie(_cookie(request))
    return {"ok": True}
