import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

logger = logging.getLogger(__name__)

from auth import USERS, get_current_user, router as auth_router
from database import (
    create_card,
    delete_card,
    ensure_user,
    get_board,
    init_db,
    move_card,
    rename_column,
    update_card,
)

# Cache user_id per username to avoid a DB query on every request
_user_id_cache: dict[str, int] = {}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    for username, password in USERS.items():
        _user_id_cache[username] = ensure_user(username, password)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)

STATIC_DIR = Path(__file__).parent / "static"


def get_user_id(username: str = Depends(get_current_user)) -> int:
    if username in _user_id_cache:
        return _user_id_cache[username]
    uid = ensure_user(username, USERS[username])
    _user_id_cache[username] = uid
    return uid


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/board")
def read_board(user_id: int = Depends(get_user_id)):
    return get_board(user_id)


class RenameColumnRequest(BaseModel):
    title: str


@app.put("/api/columns/{column_id}")
def api_rename_column(column_id: int, req: RenameColumnRequest, user_id: int = Depends(get_user_id)):
    if not rename_column(column_id, req.title, user_id):
        raise HTTPException(status_code=404, detail="Column not found")
    return {"ok": True}


class CreateCardRequest(BaseModel):
    column_id: int
    title: str
    details: str = ""


@app.post("/api/cards")
def api_create_card(req: CreateCardRequest, user_id: int = Depends(get_user_id)):
    card = create_card(req.column_id, req.title, req.details, user_id)
    if not card:
        raise HTTPException(status_code=404, detail="Column not found")
    return card


class UpdateCardRequest(BaseModel):
    title: str | None = None
    details: str | None = None


@app.put("/api/cards/{card_id}")
def api_update_card(card_id: int, req: UpdateCardRequest, user_id: int = Depends(get_user_id)):
    if not update_card(card_id, req.title, req.details, user_id):
        raise HTTPException(status_code=404, detail="Card not found")
    return {"ok": True}


@app.delete("/api/cards/{card_id}")
def api_delete_card(card_id: int, user_id: int = Depends(get_user_id)):
    if not delete_card(card_id, user_id):
        raise HTTPException(status_code=404, detail="Card not found")
    return {"ok": True}


class MoveCardRequest(BaseModel):
    target_column_id: int
    position: int


@app.put("/api/cards/{card_id}/move")
def api_move_card(card_id: int, req: MoveCardRequest, user_id: int = Depends(get_user_id)):
    if req.position < 0:
        raise HTTPException(status_code=400, detail="Position must be >= 0")
    try:
        moved = move_card(card_id, req.target_column_id, req.position, user_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    if not moved:
        raise HTTPException(status_code=404, detail="Card or column not found")
    return {"ok": True}


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[ChatMessage] = Field(default_factory=list)


class AddCardUpdate(BaseModel):
    action: Literal["add_card"]
    column_id: int
    title: str
    details: str = ""


class UpdateCardUpdate(BaseModel):
    action: Literal["update_card"]
    card_id: int
    title: str | None = None
    details: str | None = None


class MoveCardUpdate(BaseModel):
    action: Literal["move_card"]
    card_id: int
    target_column_id: int
    position: int


class DeleteCardUpdate(BaseModel):
    action: Literal["delete_card"]
    card_id: int


BoardUpdate = AddCardUpdate | UpdateCardUpdate | MoveCardUpdate | DeleteCardUpdate
BOARD_UPDATE_ADAPTER = TypeAdapter(list[BoardUpdate])


@app.post("/api/ai/chat")
def ai_chat(req: ChatRequest, user_id: int = Depends(get_user_id)):
    from ai import build_messages, chat, parse_response

    board = get_board(user_id)
    history = [item.model_dump() for item in req.conversation_history]
    messages = build_messages(board, req.message, history)

    try:
        raw = chat(messages)
    except Exception as exc:
        logger.exception("AI chat request failed")
        raise HTTPException(status_code=502, detail="AI service unavailable") from exc

    result = parse_response(raw)

    try:
        updates = BOARD_UPDATE_ADAPTER.validate_python(result.get("board_updates", []))
    except ValidationError as err:
        raise HTTPException(status_code=502, detail="Invalid AI board update payload") from err

    errors: list[str] = []
    for update in updates:
        if isinstance(update, AddCardUpdate):
            create_card(update.column_id, update.title, update.details, user_id)
        elif isinstance(update, UpdateCardUpdate):
            update_card(update.card_id, update.title, update.details, user_id)
        elif isinstance(update, MoveCardUpdate):
            try:
                move_card(update.card_id, update.target_column_id, update.position, user_id)
            except ValueError as e:
                errors.append(str(e))
        elif isinstance(update, DeleteCardUpdate):
            delete_card(update.card_id, user_id)

    updated_board = get_board(user_id)
    response = {
        "message": result["message"],
        "board_updates": [update.model_dump() for update in updates],
        "board": updated_board,
    }
    if errors:
        response["errors"] = errors
    return response


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
