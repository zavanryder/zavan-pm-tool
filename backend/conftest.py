import pytest

import database
from auth import USERS


@pytest.fixture
def user_id(tmp_path):
    database.DB_PATH = tmp_path / "test.db"
    database.init_db()
    return database.ensure_user("user", USERS["user"])
