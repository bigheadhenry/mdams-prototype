from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..permissions import CurrentUserDep, get_current_user
from ..schemas import AuthContextResponse, AuthLoginRequest, AuthLoginResponse, AuthRoleResponse, AuthUserSummary
from ..services.auth import authenticate_user, create_user_session, delete_session_token

router = APIRouter(prefix="/auth", tags=["auth"])
SESSION_COOKIE_NAME = "mdams.session"


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
def list_auth_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        AuthUserSummary(
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
def login(payload: AuthLoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username.strip(), payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    session = create_user_session(db, user)
    context = get_current_user(db=db, authorization=f"Bearer {session.session_token}")
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session.session_token,
        httponly=True,
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
