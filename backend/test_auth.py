from hashlib import sha256

import pytest
from fastapi import HTTPException

from auth import LoginRequest, RegisterRequest, create_token, get_current_user, login, me, register
from main import health
import database


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    database.DB_PATH = tmp_path / "test.db"
    database.init_db()
    database.create_user("user", "password")


def test_login_success():
    data = login(LoginRequest(username="user", password="password"))
    assert data.token
    assert data.username == "user"
    assert data.user_id > 0


def test_login_wrong_password():
    with pytest.raises(HTTPException) as exc:
        login(LoginRequest(username="user", password="wrong"))
    assert exc.value.status_code == 401


def test_login_wrong_username():
    with pytest.raises(HTTPException) as exc:
        login(LoginRequest(username="nobody", password="password"))
    assert exc.value.status_code == 401


def test_register_success():
    data = register(RegisterRequest(username="newuser", password="pass123"))
    assert data.token
    assert data.username == "newuser"
    assert data.user_id > 0


def test_register_duplicate_username():
    with pytest.raises(HTTPException) as exc:
        register(RegisterRequest(username="user", password="pass123"))
    assert exc.value.status_code == 409


def test_register_short_username():
    with pytest.raises(HTTPException) as exc:
        register(RegisterRequest(username="a", password="pass123"))
    assert exc.value.status_code == 400


def test_register_short_password():
    with pytest.raises(HTTPException) as exc:
        register(RegisterRequest(username="newuser", password="ab"))
    assert exc.value.status_code == 400


def test_register_then_login():
    register(RegisterRequest(username="fresh", password="mypass"))
    data = login(LoginRequest(username="fresh", password="mypass"))
    assert data.username == "fresh"


def test_me_with_valid_token():
    uid = database.verify_user("user", "password")
    token = create_token(uid, "user")
    current = get_current_user(f"Bearer {token}")
    result = me(current)
    assert result.username == "user"
    assert result.user_id == uid


def test_me_with_invalid_token():
    with pytest.raises(HTTPException) as exc:
        get_current_user("Bearer invalid")
    assert exc.value.status_code == 401


def test_legacy_sha256_password_is_upgraded_on_login():
    uid = database.create_user("legacy", "secret")
    legacy_hash = sha256("secret".encode()).hexdigest()
    conn = database.get_conn()
    try:
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (legacy_hash, uid))
        conn.commit()
    finally:
        conn.close()

    data = login(LoginRequest(username="legacy", password="secret"))
    assert data.username == "legacy"

    conn = database.get_conn()
    try:
        row = conn.execute("SELECT password FROM users WHERE id = ?", (uid,)).fetchone()
        assert row["password"].startswith(f"{database.PASSWORD_SCHEME}$")
        assert row["password"] != legacy_hash
    finally:
        conn.close()


def test_health():
    assert health() == {"status": "ok"}
