import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy.orm import Session

from .. import config as app_config
from ..database import get_db
from ..models import User
from ..permissions import CurrentUser, CurrentUserDep, get_current_user, require_permission
from ..schemas import AuthContextResponse, AuthLoginRequest, AuthLoginResponse, AuthRoleResponse, AuthUserSummary
from ..services.auth import authenticate_user, create_user_session, delete_session_token

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)
SESSION_COOKIE_NAME = "mdams.session"

# Simple in-memory rate limiter for login attempts
_LOGIN_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
_LOGIN_MAX_ATTEMPTS = 10
_LOGIN_WINDOW_SECONDS = 60


def _check_login_rate_limit(key: str) -> bool:
    """Return True if the request is allowed, False if rate-limited."""
    now = time.time()
    window = _LOGIN_ATTEMPTS[key]
    _LOGIN_ATTEMPTS[key] = [t for t in window if now - t < _LOGIN_WINDOW_SECONDS]
    if len(_LOGIN_ATTEMPTS[key]) >= _LOGIN_MAX_ATTEMPTS:
        return False
    _LOGIN_ATTEMPTS[key].append(now)
    return True


def _serialize_context(user) -> AuthContextResponse:
    return AuthContextResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        roles=sorted(user.roles),
        permissions=sorted(user.permissions),
        collection_scope=sorted(user.collection_scope),
        auth_mode=user.auth_mode,
    )


@router.get("/context", response_model=AuthContextResponse)
def get_auth_context(user: CurrentUserDep):
    return _serialize_context(user)


@router.get("/users", response_model=list[AuthUserSummary])
def list_auth_users(
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(require_permission("system.manage")),
):
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        AuthUserSummary(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            roles=[
                AuthRoleResponse(
                    key=user_role.role.key,
                    label=user_role.role.label,
                )
                for user_role in user.roles
                if user_role.role is not None
            ],
            collection_scope=[int(item) for item in (user.collection_scope or []) if isinstance(item, int)],
        )
        for user in users
        if user.is_active
    ]


@router.post("/login", response_model=AuthLoginResponse)
def login(payload: AuthLoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{payload.username.strip().lower()}"
    if not _check_login_rate_limit(rate_key):
        logger.warning("Login rate limit exceeded for %s from %s", payload.username, client_ip)
        raise HTTPException(status_code=429, detail="Too many login attempts, try again later")
    user = authenticate_user(db, payload.username.strip(), payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    session = create_user_session(db, user)
    context = get_current_user(db=db, authorization=f"Bearer {session.session_token}")
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.session_token,
        httponly=True,
        secure=getattr(app_config, "SESSION_COOKIE_SECURE", True),
        samesite="lax",
        path="/",
        max_age=60 * 60 * 12,
    )
    return AuthLoginResponse(token=session.session_token, user=_serialize_context(context))


@router.post("/logout")
def logout(
    response: Response,
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            delete_session_token(db, token.strip())
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}
