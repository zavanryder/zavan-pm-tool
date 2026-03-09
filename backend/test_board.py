import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Use a temp database for tests
_tmpdir = tempfile.mkdtemp()

import database
database.DB_PATH = database.Path(_tmpdir) / "test.db"
database.init_db()

from auth import USERS
database.ensure_user("user", USERS["user"])

from main import app

client = TestClient(app)


def get_token() -> str:
    r = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    return r.json()["token"]


def auth_headers():
    return {"Authorization": f"Bearer {get_token()}"}


def test_get_board_requires_auth():
    r = client.get("/api/board")
    assert r.status_code in (401, 422)


def test_get_board():
    r = client.get("/api/board", headers=auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert "columns" in data
    assert len(data["columns"]) == 5
    titles = [c["title"] for c in data["columns"]]
    assert titles == ["Backlog", "Discovery", "In Progress", "Review", "Done"]


def test_rename_column():
    headers = auth_headers()
    board = client.get("/api/board", headers=headers).json()
    col_id = board["columns"][0]["id"]
    r = client.put(f"/api/columns/{col_id}", json={"title": "Todo"}, headers=headers)
    assert r.status_code == 200
    board = client.get("/api/board", headers=headers).json()
    assert board["columns"][0]["title"] == "Todo"


def test_rename_column_not_found():
    r = client.put("/api/columns/9999", json={"title": "X"}, headers=auth_headers())
    assert r.status_code == 404


def test_create_card():
    headers = auth_headers()
    board = client.get("/api/board", headers=headers).json()
    col_id = board["columns"][0]["id"]
    r = client.post("/api/cards", json={"column_id": col_id, "title": "Test Card", "details": "Some details"}, headers=headers)
    assert r.status_code == 200
    card = r.json()
    assert card["title"] == "Test Card"
    assert "id" in card

    board = client.get("/api/board", headers=headers).json()
    card_titles = [c["title"] for c in board["columns"][0]["cards"]]
    assert "Test Card" in card_titles


def test_create_card_invalid_column():
    r = client.post("/api/cards", json={"column_id": 9999, "title": "X"}, headers=auth_headers())
    assert r.status_code == 404


def test_update_card():
    headers = auth_headers()
    board = client.get("/api/board", headers=headers).json()
    col_id = board["columns"][1]["id"]
    card = client.post("/api/cards", json={"column_id": col_id, "title": "Original"}, headers=headers).json()
    r = client.put(f"/api/cards/{card['id']}", json={"title": "Updated", "details": "New details"}, headers=headers)
    assert r.status_code == 200

    board = client.get("/api/board", headers=headers).json()
    updated = [c for c in board["columns"][1]["cards"] if c["id"] == card["id"]][0]
    assert updated["title"] == "Updated"
    assert updated["details"] == "New details"


def test_update_card_not_found():
    r = client.put("/api/cards/9999", json={"title": "X"}, headers=auth_headers())
    assert r.status_code == 404


def test_delete_card():
    headers = auth_headers()
    board = client.get("/api/board", headers=headers).json()
    col_id = board["columns"][2]["id"]
    card = client.post("/api/cards", json={"column_id": col_id, "title": "ToDelete"}, headers=headers).json()
    r = client.delete(f"/api/cards/{card['id']}", headers=headers)
    assert r.status_code == 200

    board = client.get("/api/board", headers=headers).json()
    card_ids = [c["id"] for c in board["columns"][2]["cards"]]
    assert card["id"] not in card_ids


def test_delete_card_not_found():
    r = client.delete("/api/cards/9999", headers=auth_headers())
    assert r.status_code == 404


def test_move_card():
    headers = auth_headers()
    board = client.get("/api/board", headers=headers).json()
    src_col_id = board["columns"][0]["id"]
    dst_col_id = board["columns"][3]["id"]

    card = client.post("/api/cards", json={"column_id": src_col_id, "title": "Mover"}, headers=headers).json()
    r = client.put(f"/api/cards/{card['id']}/move", json={"target_column_id": dst_col_id, "position": 0}, headers=headers)
    assert r.status_code == 200

    board = client.get("/api/board", headers=headers).json()
    src_ids = [c["id"] for c in board["columns"][0]["cards"]]
    dst_ids = [c["id"] for c in board["columns"][3]["cards"]]
    assert card["id"] not in src_ids
    assert card["id"] in dst_ids


def test_move_card_not_found():
    headers = auth_headers()
    r = client.put("/api/cards/9999/move", json={"target_column_id": 1, "position": 0}, headers=headers)
    assert r.status_code == 404
