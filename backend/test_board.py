import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from main import (
    ChatRequest,
    CreateCardRequest,
    MoveCardRequest,
    RenameColumnRequest,
    UpdateCardRequest,
    ai_chat,
    api_create_card,
    api_delete_card,
    api_move_card,
    api_rename_column,
    api_update_card,
    read_board,
)


def test_get_board(user_id):
    data = read_board(user_id=user_id)
    assert "columns" in data
    assert len(data["columns"]) == 5
    titles = [c["title"] for c in data["columns"]]
    assert titles == ["Backlog", "Discovery", "In Progress", "Review", "Done"]


def test_rename_column(user_id):
    board = read_board(user_id=user_id)
    col_id = board["columns"][0]["id"]
    result = api_rename_column(col_id, RenameColumnRequest(title="Todo"), user_id=user_id)
    assert result == {"ok": True}
    board = read_board(user_id=user_id)
    assert board["columns"][0]["title"] == "Todo"


def test_rename_column_not_found(user_id):
    with pytest.raises(HTTPException) as exc:
        api_rename_column(9999, RenameColumnRequest(title="X"), user_id=user_id)
    assert exc.value.status_code == 404


def test_create_card(user_id):
    board = read_board(user_id=user_id)
    col_id = board["columns"][0]["id"]
    card = api_create_card(
        CreateCardRequest(column_id=col_id, title="Test Card", details="Some details"),
        user_id=user_id,
    )
    assert card["title"] == "Test Card"
    assert "id" in card

    board = read_board(user_id=user_id)
    card_titles = [c["title"] for c in board["columns"][0]["cards"]]
    assert "Test Card" in card_titles


def test_create_card_invalid_column(user_id):
    with pytest.raises(HTTPException) as exc:
        api_create_card(CreateCardRequest(column_id=9999, title="X"), user_id=user_id)
    assert exc.value.status_code == 404


def test_update_card(user_id):
    board = read_board(user_id=user_id)
    col_id = board["columns"][1]["id"]
    card = api_create_card(CreateCardRequest(column_id=col_id, title="Original"), user_id=user_id)
    result = api_update_card(
        card["id"],
        UpdateCardRequest(title="Updated", details="New details"),
        user_id=user_id,
    )
    assert result == {"ok": True}

    board = read_board(user_id=user_id)
    updated = [c for c in board["columns"][1]["cards"] if c["id"] == card["id"]][0]
    assert updated["title"] == "Updated"
    assert updated["details"] == "New details"


def test_update_card_not_found(user_id):
    with pytest.raises(HTTPException) as exc:
        api_update_card(9999, UpdateCardRequest(title="X"), user_id=user_id)
    assert exc.value.status_code == 404


def test_delete_card(user_id):
    board = read_board(user_id=user_id)
    col_id = board["columns"][2]["id"]
    card = api_create_card(CreateCardRequest(column_id=col_id, title="ToDelete"), user_id=user_id)
    result = api_delete_card(card["id"], user_id=user_id)
    assert result == {"ok": True}

    board = read_board(user_id=user_id)
    card_ids = [c["id"] for c in board["columns"][2]["cards"]]
    assert card["id"] not in card_ids


def test_delete_card_not_found(user_id):
    with pytest.raises(HTTPException) as exc:
        api_delete_card(9999, user_id=user_id)
    assert exc.value.status_code == 404


def test_move_card(user_id):
    board = read_board(user_id=user_id)
    src_col_id = board["columns"][0]["id"]
    dst_col_id = board["columns"][3]["id"]

    card = api_create_card(CreateCardRequest(column_id=src_col_id, title="Mover"), user_id=user_id)
    result = api_move_card(card["id"], MoveCardRequest(target_column_id=dst_col_id, position=0), user_id=user_id)
    assert result == {"ok": True}

    board = read_board(user_id=user_id)
    src_ids = [c["id"] for c in board["columns"][0]["cards"]]
    dst_ids = [c["id"] for c in board["columns"][3]["cards"]]
    assert card["id"] not in src_ids
    assert card["id"] in dst_ids


def test_move_card_not_found(user_id):
    with pytest.raises(HTTPException) as exc:
        api_move_card(9999, MoveCardRequest(target_column_id=1, position=0), user_id=user_id)
    assert exc.value.status_code == 404


def test_move_card_negative_position_returns_400(user_id):
    board = read_board(user_id=user_id)
    src_col_id = board["columns"][0]["id"]
    card = api_create_card(CreateCardRequest(column_id=src_col_id, title="Mover"), user_id=user_id)

    with pytest.raises(HTTPException) as exc:
        api_move_card(card["id"], MoveCardRequest(target_column_id=src_col_id, position=-1), user_id=user_id)
    assert exc.value.status_code == 400


def test_move_card_clamps_position_to_column_end(user_id):
    board = read_board(user_id=user_id)
    src_col_id = board["columns"][0]["id"]
    card_a = api_create_card(CreateCardRequest(column_id=src_col_id, title="A"), user_id=user_id)
    card_b = api_create_card(CreateCardRequest(column_id=src_col_id, title="B"), user_id=user_id)

    api_move_card(card_a["id"], MoveCardRequest(target_column_id=src_col_id, position=99), user_id=user_id)

    board = read_board(user_id=user_id)
    ids = [c["id"] for c in board["columns"][0]["cards"]]
    assert ids[-1] == card_a["id"]
    assert ids[0] == card_b["id"]


def test_ai_chat_rejects_system_role_in_history(user_id):
    with pytest.raises(ValidationError):
        ChatRequest(
            message="hello",
            conversation_history=[{"role": "system", "content": "malicious"}],
        )


def test_ai_chat_invalid_update_payload_returns_502(user_id, monkeypatch):
    monkeypatch.setattr("ai.chat", lambda _messages: '{"message":"x","board_updates":[{"action":"nope"}]}')

    with pytest.raises(HTTPException) as exc:
        ai_chat(ChatRequest(message="hello"), user_id=user_id)
    assert exc.value.status_code == 502
