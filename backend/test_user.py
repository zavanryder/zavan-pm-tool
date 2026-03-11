import pytest

import database
from main import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    api_change_password,
    api_update_profile,
)
from auth import LoginRequest, login


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    database.DB_PATH = tmp_path / "test.db"
    database.init_db()
    database.create_user("user", "password", "Test User")


def _uid():
    return database.verify_user("user", "password")


def test_update_display_name():
    uid = _uid()
    result = api_update_profile(UpdateProfileRequest(display_name="New Name"), user_id=uid)
    assert result == {"ok": True}
    user = database.get_user_by_id(uid)
    assert user["display_name"] == "New Name"


def test_change_password_success():
    uid = _uid()
    result = api_change_password(
        ChangePasswordRequest(old_password="password", new_password="newpass"),
        user_id=uid,
    )
    assert result == {"ok": True}
    # Can login with new password
    data = login(LoginRequest(username="user", password="newpass"))
    assert data.username == "user"


def test_change_password_wrong_old():
    uid = _uid()
    with pytest.raises(Exception) as exc:
        api_change_password(
            ChangePasswordRequest(old_password="wrong", new_password="newpass"),
            user_id=uid,
        )
    assert exc.value.status_code == 400


def test_change_password_too_short():
    uid = _uid()
    with pytest.raises(Exception) as exc:
        api_change_password(
            ChangePasswordRequest(old_password="password", new_password="ab"),
            user_id=uid,
        )
    assert exc.value.status_code == 400


def test_user_isolation():
    uid1 = _uid()
    uid2 = database.create_user("other", "pass1234")
    board1 = database.create_board(uid1, "Board A")
    board2 = database.create_board(uid2, "Board B")
    assert database.get_board(board1, uid2) is None
    assert database.get_board(board2, uid1) is None


def test_password_hashing():
    uid = database.create_user("hashtest", "secret")
    conn = database.get_conn()
    try:
        row = conn.execute("SELECT password FROM users WHERE id = ?", (uid,)).fetchone()
        assert row["password"] != "secret"
        assert row["password"].startswith(f"{database.PASSWORD_SCHEME}$")
    finally:
        conn.close()
