from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
from time import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session as DBSession
from sqlmodel import select

from ..db import Repo
from ..deps import get_repo
from ..models.auth import Account, AccountPublic, Credentials, LoginSession

router = APIRouter(prefix="/api/auth")
COOKIE = "rep_trainer_session"
SESSION_SECONDS = 7 * 24 * 3600
ITERATIONS = 400_000
_rate_lock = threading.Lock()
_attempts: dict[str, list[float]] = {}


def _error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": {"code": code, "message": message}})


def _rate_limit(request: Request, action: str, key: str, max_count: int, window: int) -> None:
    ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")
    bucket = f"{action}:{ip}:{key}"
    now = time()
    with _rate_lock:
        if len(_attempts) > 2000:
            for stale in [name for name, times in _attempts.items() if times[-1] < now - 3600]:
                del _attempts[stale]
        recent = [t for t in _attempts.get(bucket, []) if t > now - window]
        if len(recent) >= max_count:
            raise _error(429, "rate_limited", "尝试次数过多，请稍后重试")
        recent.append(now)
        _attempts[bucket] = recent


def _password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}"


def _password_matches(password: str, stored: str) -> bool:
    try:
        algorithm, count, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256" or not 100_000 <= int(count) <= 1_000_000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(count))
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _cookie_path(request: Request) -> str:
    return "/rep-trainer/" if request.headers.get("x-forwarded-prefix") == "/rep-trainer" else "/"


def _issue_session(account: Account, response: Response, request: Request, repo: Repo) -> AccountPublic:
    token = secrets.token_urlsafe(32)
    with DBSession(repo.engine) as db:
        db.add(LoginSession(token_hash=_token_hash(token), account_id=account.id,
                            expires_at=int(time()) + SESSION_SECONDS))
        db.commit()
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, path=_cookie_path(request),
                        secure=request.headers.get("x-forwarded-proto", request.url.scheme) == "https",
                        httponly=True, samesite="lax")
    return AccountPublic(id=account.id, username=account.username)


def get_current_account(request: Request, repo: Repo = Depends(get_repo)) -> Account:
    token = request.cookies.get(COOKIE)
    if not token:
        raise _error(401, "not_authenticated", "请先登录")
    with DBSession(repo.engine) as db:
        login = db.get(LoginSession, _token_hash(token))
        account = db.get(Account, login.account_id) if login and login.expires_at > int(time()) else None
        if not account:
            raise _error(401, "not_authenticated", "登录已过期，请重新登录")
        return account


@router.post("/register", response_model=AccountPublic)
def register(body: Credentials, request: Request, response: Response, repo: Repo = Depends(get_repo)):
    _rate_limit(request, "register", "all", 10, 3600)
    account = Account(id=f"usr_{uuid4().hex}", username=body.username,
                      password_hash=_password_hash(body.password))
    try:
        with DBSession(repo.engine, expire_on_commit=False) as db:
            db.add(account)
            db.commit()
    except IntegrityError as exc:
        raise _error(409, "username_taken", "这个账号已被使用") from exc
    return _issue_session(account, response, request, repo)


@router.post("/login", response_model=AccountPublic)
def login(body: Credentials, request: Request, response: Response, repo: Repo = Depends(get_repo)):
    _rate_limit(request, "login", "all", 100, 900)
    _rate_limit(request, "login", body.username, 20, 900)
    with DBSession(repo.engine) as db:
        account = db.exec(select(Account).where(Account.username == body.username)).first()
    if not account or not _password_matches(body.password, account.password_hash):
        raise _error(401, "invalid_credentials", "账号或密码不正确")
    return _issue_session(account, response, request, repo)


@router.get("/me", response_model=AccountPublic)
def me(account: Account = Depends(get_current_account)):
    return AccountPublic(id=account.id, username=account.username)


@router.get("/check", status_code=204)
def check(account: Account = Depends(get_current_account)):
    return Response(status_code=204)


@router.post("/logout")
def logout(request: Request, response: Response, repo: Repo = Depends(get_repo)):
    token = request.cookies.get(COOKIE)
    if token:
        with DBSession(repo.engine) as db:
            login_session = db.get(LoginSession, _token_hash(token))
            if login_session:
                db.delete(login_session)
                db.commit()
    response.delete_cookie(COOKIE, path=_cookie_path(request), samesite="lax")
    return {"ok": True}
