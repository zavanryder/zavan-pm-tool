from unittest.mock import patch, MagicMock

from ai import chat, build_messages, parse_response, MODEL


def test_chat_calls_openai_correctly():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "4"

    with patch("ai.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get.return_value = mock_client

        result = chat([{"role": "user", "content": "What is 2+2?"}])

        assert result == "4"
        mock_client.chat.completions.create.assert_called_once_with(
            model=MODEL,
            messages=[{"role": "user", "content": "What is 2+2?"}],
        )


def test_build_messages_includes_board():
    board = {"id": 1, "columns": [{"id": 1, "title": "Backlog", "cards": []}]}
    msgs = build_messages(board, "Hello", [])
    assert msgs[0]["role"] == "system"
    assert "Backlog" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"
    assert msgs[1]["content"] == "Hello"


def test_build_messages_includes_history():
    board = {"id": 1, "columns": []}
    history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]
    msgs = build_messages(board, "What?", history)
    assert len(msgs) == 4  # system + 2 history + user
    assert msgs[1]["content"] == "Hi"
    assert msgs[3]["content"] == "What?"


def test_parse_response_valid_json():
    raw = '{"message": "Done!", "board_updates": [{"action": "add_card", "column_id": 1, "title": "New", "details": ""}]}'
    result = parse_response(raw)
    assert result["message"] == "Done!"
    assert len(result["board_updates"]) == 1
    assert result["board_updates"][0]["action"] == "add_card"


def test_parse_response_no_updates():
    raw = '{"message": "Just chatting"}'
    result = parse_response(raw)
    assert result["message"] == "Just chatting"
    assert result["board_updates"] == []


def test_parse_response_malformed():
    raw = "Sorry, I don't understand"
    result = parse_response(raw)
    assert result["message"] == raw
    assert result["board_updates"] == []


def test_parse_response_code_fenced():
    raw = '```json\n{"message": "Hello", "board_updates": []}\n```'
    result = parse_response(raw)
    assert result["message"] == "Hello"
    assert result["board_updates"] == []
