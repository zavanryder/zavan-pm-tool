import pytest

import database


@pytest.fixture
def user_id(tmp_path):
    database.DB_PATH = tmp_path / "test.db"
    database.init_db()
    return database.create_user("user", "password")


@pytest.fixture
def second_user_id(tmp_path):
    """Second user for isolation tests. Requires user_id fixture to init db first."""
    return database.create_user("user2", "password2")
