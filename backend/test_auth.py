import pytest
from fastapi import HTTPException

from auth import LoginRequest, create_token, get_current_user, login, me
from main import health


def test_login_success():
    data = login(LoginRequest(username="user", password="password"))
    assert data.token
    assert data.username == "user"


def test_login_wrong_password():
    with pytest.raises(HTTPException) as exc:
        login(LoginRequest(username="user", password="wrong"))
    assert exc.value.status_code == 401


def test_login_wrong_username():
    with pytest.raises(HTTPException) as exc:
        login(LoginRequest(username="nobody", password="password"))
    assert exc.value.status_code == 401


def test_me_with_valid_token():
    token = create_token("user")
    username = get_current_user(f"Bearer {token}")
    result = me(username)
    assert result.username == "user"


def test_me_with_invalid_token():
    with pytest.raises(HTTPException) as exc:
        get_current_user("Bearer invalid")
    assert exc.value.status_code == 401


def test_health():
    assert health() == {"status": "ok"}
