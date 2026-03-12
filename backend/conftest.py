import pytest

import database


@pytest.fixture
def user_id(tmp_path):
    database.DB_PATH = tmp_path / "test.db"
    database.init_db()
    return database.create_user("user", "password")


@pytest.fixture
def second_user_id(user_id):
    """Second user for isolation tests."""
    return database.create_user("user2", "password2")
