import json
import os

from openai import OpenAI

MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are an AI assistant for a Kanban board app called Kanban Studio.

The user's current board state is provided below as JSON. Each column has an id, title, and list of cards. Each card has an id, title, and details.

BOARD STATE:
{board_json}

You can help the user by:
1. Answering questions about their board
2. Making changes to the board (add, update, move, or delete cards)

IMPORTANT: You must respond with valid JSON in this exact format:
{{
  "message": "Your response to the user",
  "board_updates": []
}}

The board_updates array can contain zero or more operations:
- {{"action": "add_card", "column_id": <number>, "title": "<string>", "details": "<string>"}}
- {{"action": "update_card", "card_id": <number>, "title": "<string>", "details": "<string>"}}
- {{"action": "move_card", "card_id": <number>, "target_column_id": <number>, "position": <number>}}
- {{"action": "delete_card", "card_id": <number>}}

If the user is just chatting and no board changes are needed, return an empty board_updates array.
Always respond with valid JSON. No markdown, no code fences, just raw JSON."""

ALLOWED_HISTORY_ROLES = {"user", "assistant"}


def get_client() -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )


def chat(messages: list[dict]) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    return response.choices[0].message.content or ""


def build_messages(board: dict, user_message: str, history: list[dict]) -> list[dict]:
    board_json = json.dumps(board, indent=2)
    system = SYSTEM_PROMPT.format(board_json=board_json)
    messages = [{"role": "system", "content": system}]

    # Ignore forged/invalid history roles to avoid user-provided system prompt injection.
    for entry in history:
        if not isinstance(entry, dict):
            continue
        role = entry.get("role")
        content = entry.get("content")
        if role in ALLOWED_HISTORY_ROLES and isinstance(content, str):
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})
    return messages


def parse_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "message" in data:
            return {
                "message": data["message"],
                "board_updates": data.get("board_updates", []),
            }
    except (json.JSONDecodeError, KeyError):
        pass
    return {"message": raw, "board_updates": []}
