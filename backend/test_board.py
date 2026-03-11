import pytest
from fastapi import HTTPException
from pydantic import ValidationError

import database
from main import (
    AddColumnRequest,
    ChatRequest,
    CreateBoardRequest,
    CreateCardRequest,
    MoveCardRequest,
    RenameBoardRequest,
    RenameColumnRequest,
    SearchRequest,
    UpdateCardRequest,
    ai_chat,
    api_add_column,
    api_create_board,
    api_create_card,
    api_delete_board,
    api_delete_card,
    api_delete_column,
    api_get_board,
    api_list_boards,
    api_move_card,
    api_rename_board,
    api_rename_column,
    api_search,
    api_update_card,
    read_board,
)


# --- Legacy single-board endpoint ---

def test_get_board(user_id):
    data = read_board(user_id=user_id)
    assert "columns" in data
    assert len(data["columns"]) == 5
    titles = [c["title"] for c in data["columns"]]
    assert titles == ["Backlog", "Discovery", "In Progress", "Review", "Done"]


# --- Multi-board CRUD ---

def test_create_board(user_id):
    board = api_create_board(CreateBoardRequest(name="Sprint 1"), user_id=user_id)
    assert board["name"] == "Sprint 1"
    assert len(board["columns"]) == 5


def test_create_board_limit_returns_400(user_id, monkeypatch):
    monkeypatch.setattr(database, "MAX_BOARDS_PER_USER", 1)
    api_create_board(CreateBoardRequest(name="First"), user_id=user_id)
    with pytest.raises(HTTPException) as exc:
        api_create_board(CreateBoardRequest(name="Second"), user_id=user_id)
    assert exc.value.status_code == 400


def test_list_boards(user_id):
    # Legacy endpoint creates a default board
    read_board(user_id=user_id)
    api_create_board(CreateBoardRequest(name="Second"), user_id=user_id)
    boards = api_list_boards(user_id=user_id)
    assert len(boards) == 2
    names = [b["name"] for b in boards]
    assert "My Board" in names
    assert "Second" in names


def test_rename_board(user_id):
    board = api_create_board(CreateBoardRequest(name="Old Name"), user_id=user_id)
    result = api_rename_board(board["id"], RenameBoardRequest(name="New Name"), user_id=user_id)
    assert result == {"ok": True}
    updated = api_get_board(board["id"], user_id=user_id)
    assert updated["name"] == "New Name"


def test_rename_board_not_found(user_id):
    with pytest.raises(HTTPException) as exc:
        api_rename_board(9999, RenameBoardRequest(name="X"), user_id=user_id)
    assert exc.value.status_code == 404


def test_delete_board(user_id):
    board = api_create_board(CreateBoardRequest(name="Temp"), user_id=user_id)
    result = api_delete_board(board["id"], user_id=user_id)
    assert result == {"ok": True}
    with pytest.raises(HTTPException) as exc:
        api_get_board(board["id"], user_id=user_id)
    assert exc.value.status_code == 404


def test_delete_board_not_found(user_id):
    with pytest.raises(HTTPException) as exc:
        api_delete_board(9999, user_id=user_id)
    assert exc.value.status_code == 404


def test_get_board_by_id(user_id):
    board = api_create_board(CreateBoardRequest(name="Specific"), user_id=user_id)
    fetched = api_get_board(board["id"], user_id=user_id)
    assert fetched["name"] == "Specific"
    assert len(fetched["columns"]) == 5


def test_board_isolation(user_id, second_user_id):
    board = api_create_board(CreateBoardRequest(name="Private"), user_id=user_id)
    with pytest.raises(HTTPException) as exc:
        api_get_board(board["id"], user_id=second_user_id)
    assert exc.value.status_code == 404


# --- Column management ---

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


def test_add_column(user_id):
    board = api_create_board(CreateBoardRequest(name="Test"), user_id=user_id)
    col = api_add_column(AddColumnRequest(board_id=board["id"], title="Extra"), user_id=user_id)
    assert col["title"] == "Extra"
    assert col["position"] == 5
    updated = api_get_board(board["id"], user_id=user_id)
    assert len(updated["columns"]) == 6


def test_add_column_limit_returns_400(user_id, monkeypatch):
    board = api_create_board(CreateBoardRequest(name="Test"), user_id=user_id)
    monkeypatch.setattr(database, "MAX_COLUMNS_PER_BOARD", len(board["columns"]))
    with pytest.raises(HTTPException) as exc:
        api_add_column(AddColumnRequest(board_id=board["id"], title="Overflow"), user_id=user_id)
    assert exc.value.status_code == 400


def test_add_column_invalid_board(user_id):
    with pytest.raises(HTTPException) as exc:
        api_add_column(AddColumnRequest(board_id=9999, title="X"), user_id=user_id)
    assert exc.value.status_code == 404


def test_delete_column(user_id):
    board = api_create_board(CreateBoardRequest(name="Test"), user_id=user_id)
    col_id = board["columns"][4]["id"]
    result = api_delete_column(col_id, user_id=user_id)
    assert result == {"ok": True}
    updated = api_get_board(board["id"], user_id=user_id)
    assert len(updated["columns"]) == 4


def test_delete_column_not_found(user_id):
    with pytest.raises(HTTPException) as exc:
        api_delete_column(9999, user_id=user_id)
    assert exc.value.status_code == 404


# --- Card CRUD ---

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


def test_create_card_with_label_and_due_date(user_id):
    board = read_board(user_id=user_id)
    col_id = board["columns"][0]["id"]
    card = api_create_card(
        CreateCardRequest(column_id=col_id, title="Labeled", label="bug", due_date="2026-04-01"),
        user_id=user_id,
    )
    assert card["label"] == "bug"
    assert card["due_date"] == "2026-04-01"


def test_create_card_invalid_column(user_id):
    with pytest.raises(HTTPException) as exc:
        api_create_card(CreateCardRequest(column_id=9999, title="X"), user_id=user_id)
    assert exc.value.status_code == 404


def test_create_card_rejects_oversized_title():
    with pytest.raises(ValidationError):
        CreateCardRequest(column_id=1, title="x" * 201)


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


def test_update_card_label(user_id):
    board = read_board(user_id=user_id)
    col_id = board["columns"][0]["id"]
    card = api_create_card(CreateCardRequest(column_id=col_id, title="Card"), user_id=user_id)
    api_update_card(card["id"], UpdateCardRequest(label="feature"), user_id=user_id)
    board = read_board(user_id=user_id)
    updated = [c for c in board["columns"][0]["cards"] if c["id"] == card["id"]][0]
    assert updated["label"] == "feature"


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


# --- Search ---

def test_search_cards(user_id):
    board = read_board(user_id=user_id)
    col_id = board["columns"][0]["id"]
    api_create_card(CreateCardRequest(column_id=col_id, title="Fix login bug"), user_id=user_id)
    api_create_card(CreateCardRequest(column_id=col_id, title="Add feature"), user_id=user_id)
    results = api_search(SearchRequest(query="login"), user_id=user_id)
    assert len(results) == 1
    assert results[0]["title"] == "Fix login bug"


def test_search_cards_empty(user_id):
    results = api_search(SearchRequest(query="nonexistent"), user_id=user_id)
    assert results == []


# --- AI chat ---

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


def test_chat_request_rejects_too_many_history_messages():
    with pytest.raises(ValidationError):
        ChatRequest(
            message="hello",
            conversation_history=[{"role": "user", "content": "x"} for _ in range(21)],
        )


def test_ai_chat_cannot_mutate_a_different_board(user_id, monkeypatch):
    board1 = api_create_board(CreateBoardRequest(name="Board 1"), user_id=user_id)
    board2 = api_create_board(CreateBoardRequest(name="Board 2"), user_id=user_id)
    other_column_id = board2["columns"][0]["id"]

    monkeypatch.setattr(
        "ai.chat",
        lambda _messages: (
            '{"message":"ok","board_updates":['
            f'{{"action":"add_card","column_id":{other_column_id},"title":"Cross-board","details":""}}'
            "]}"),
    )

    result = ai_chat(ChatRequest(message="add a card", board_id=board1["id"]), user_id=user_id)
    board1_after = api_get_board(board1["id"], user_id=user_id)
    board2_after = api_get_board(board2["id"], user_id=user_id)

    assert board1_after["columns"][0]["cards"] == []
    assert board2_after["columns"][0]["cards"] == []
    assert "errors" in result
