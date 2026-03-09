import tempfile

import pytest

import database
from auth import USERS


@pytest.fixture
def user_id():
    tmpdir = tempfile.mkdtemp()
    database.DB_PATH = database.Path(tmpdir) / "test.db"
    database.init_db()
    return database.ensure_user("user", USERS["user"])
