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
GUEST_SECONDS = 24 * 3600
GUEST_PASSWORD_MARKER = "!guest-no-password!"
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


def is_guest_account(account: Account) -> bool:
    return account.password_hash == GUEST_PASSWORD_MARKER


def _guest_route_allowed(path: str) -> bool:
    return (path in {"/api/programs", "/api/scenarios", "/api/sessions", "/api/diary/preview"}
            or path.startswith(("/api/auth/", "/api/scenarios/", "/api/sessions/", "/api/reports/", "/api/products/")))


def _public(account: Account) -> AccountPublic:
    return AccountPublic(id=account.id, username=account.username, is_guest=is_guest_account(account))


def _issue_session(account: Account, response: Response, request: Request, repo: Repo,
                   seconds: int = SESSION_SECONDS) -> AccountPublic:
    token = secrets.token_urlsafe(32)
    with DBSession(repo.engine) as db:
        db.add(LoginSession(token_hash=_token_hash(token), account_id=account.id,
                            expires_at=int(time()) + seconds))
        db.commit()
    response.set_cookie(COOKIE, token, max_age=seconds, path=_cookie_path(request),
                        secure=request.headers.get("x-forwarded-proto", request.url.scheme) == "https",
                        httponly=True, samesite="lax")
    return _public(account)


def get_current_account(request: Request, repo: Repo = Depends(get_repo)) -> Account:
    token = request.cookies.get(COOKIE)
    if not token:
        raise _error(401, "not_authenticated", "请先登录")
    with DBSession(repo.engine) as db:
        login = db.get(LoginSession, _token_hash(token))
        account = db.get(Account, login.account_id) if login and login.expires_at > int(time()) else None
        if not account:
            raise _error(401, "not_authenticated", "登录已过期，请重新登录")
        if is_guest_account(account):
            if account.created_at + GUEST_SECONDS <= int(time()):
                raise _error(401, "guest_expired", "试用已到期，请重新开始或创建账号")
            if not _guest_route_allowed(request.url.path):
                raise _error(403, "guest_limited", "试用可练习和临时整理口述；创建账号后可保存日记并使用学术雷达")
        return account


def maybe_current_account(request: Request, repo: Repo) -> Account | None:
    try:
        return get_current_account(request, repo)
    except HTTPException as exc:
        if exc.status_code == 401:
            return None
        raise


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


@router.post("/guest", response_model=AccountPublic)
def guest(request: Request, response: Response, repo: Repo = Depends(get_repo)):
    existing = maybe_current_account(request, repo)
    if existing:
        return _public(existing)
    _rate_limit(request, "guest", "all", 8, 3600)
    account = Account(id=f"usr_{uuid4().hex}", username=f"guest_{uuid4().hex[:16]}",
                      password_hash=GUEST_PASSWORD_MARKER)
    with DBSession(repo.engine, expire_on_commit=False) as db:
        db.add(account)
        db.commit()
    return _issue_session(account, response, request, repo, GUEST_SECONDS)


@router.post("/upgrade", response_model=AccountPublic)
def upgrade(body: Credentials, request: Request, response: Response,
            repo: Repo = Depends(get_repo), account: Account = Depends(get_current_account)):
    if not is_guest_account(account):
        raise _error(409, "already_registered", "当前已是正式账号")
    _rate_limit(request, "upgrade", account.id, 5, 3600)
    try:
        with DBSession(repo.engine, expire_on_commit=False) as db:
            saved = db.get(Account, account.id)
            if not saved or not is_guest_account(saved):
                raise _error(409, "already_registered", "当前已是正式账号")
            saved.username = body.username
            saved.password_hash = _password_hash(body.password)
            db.add(saved)
            old_token = request.cookies.get(COOKIE)
            old_session = db.get(LoginSession, _token_hash(old_token)) if old_token else None
            if old_session:
                db.delete(old_session)
            db.commit()
    except IntegrityError as exc:
        raise _error(409, "username_taken", "这个账号已被使用") from exc
    account.username = body.username
    account.password_hash = saved.password_hash
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
    return _public(account)


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
