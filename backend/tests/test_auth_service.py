import pytest

from app.models import Role, User
from app.services.auth import (
    DEFAULT_PASSWORD,
    authenticate_user,
    create_user_session,
    get_user_by_session_token,
    seed_auth_data,
)


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_seed_auth_data_creates_roles_and_users(db_session):
    seed_auth_data(db_session)

    assert db_session.query(Role).count() >= 9
    assert db_session.query(User).count() >= 9

    user = db_session.query(User).filter(User.username == "resource_user").first()
    assert user is not None
    assert user.display_name == "Resource User"


def test_authenticate_seeded_user_and_session(db_session):
    seed_auth_data(db_session)

    user = authenticate_user(db_session, "system_admin", DEFAULT_PASSWORD)
    assert user is not None
    assert user.username == "system_admin"

    session = create_user_session(db_session, user)
    resolved_user = get_user_by_session_token(db_session, session.session_token)

    assert resolved_user is not None
    assert resolved_user.username == "system_admin"
