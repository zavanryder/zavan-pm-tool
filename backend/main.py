import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

logger = logging.getLogger(__name__)

from auth import get_current_user, router as auth_router
from database import (
    add_column,
    change_password,
    create_board,
    create_card,
    delete_board,
    delete_card,
    delete_column,
    ensure_user,
    get_board,
    get_default_board,
    init_db,
    list_boards,
    move_card,
    rename_board,
    rename_column,
    search_cards,
    update_card,
    update_user_profile,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    # Seed default user for backwards compatibility
    ensure_user("user", "password")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)

STATIC_DIR = Path(__file__).parent / "static"


def get_user_id(current_user: dict = Depends(get_current_user)) -> int:
    return current_user["user_id"]


# --- Health ---

@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- Board CRUD ---

@app.get("/api/boards")
def api_list_boards(user_id: int = Depends(get_user_id)):
    return list_boards(user_id)


class CreateBoardRequest(BaseModel):
    name: str = "My Board"


@app.post("/api/boards")
def api_create_board(req: CreateBoardRequest, user_id: int = Depends(get_user_id)):
    board_id = create_board(user_id, req.name)
    board = get_board(board_id, user_id)
    return board


class RenameBoardRequest(BaseModel):
    name: str


@app.put("/api/boards/{board_id}")
def api_rename_board(board_id: int, req: RenameBoardRequest, user_id: int = Depends(get_user_id)):
    if not rename_board(board_id, req.name, user_id):
        raise HTTPException(status_code=404, detail="Board not found")
    return {"ok": True}


@app.delete("/api/boards/{board_id}")
def api_delete_board(board_id: int, user_id: int = Depends(get_user_id)):
    if not delete_board(board_id, user_id):
        raise HTTPException(status_code=404, detail="Board not found")
    return {"ok": True}


@app.get("/api/boards/{board_id}")
def api_get_board(board_id: int, user_id: int = Depends(get_user_id)):
    board = get_board(board_id, user_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


# Legacy single-board endpoint
@app.get("/api/board")
def read_board(user_id: int = Depends(get_user_id)):
    return get_default_board(user_id)


# --- Column management ---

class RenameColumnRequest(BaseModel):
    title: str


@app.put("/api/columns/{column_id}")
def api_rename_column(column_id: int, req: RenameColumnRequest, user_id: int = Depends(get_user_id)):
    if not rename_column(column_id, req.title, user_id):
        raise HTTPException(status_code=404, detail="Column not found")
    return {"ok": True}


class AddColumnRequest(BaseModel):
    board_id: int
    title: str


@app.post("/api/columns")
def api_add_column(req: AddColumnRequest, user_id: int = Depends(get_user_id)):
    col = add_column(req.board_id, req.title, user_id)
    if not col:
        raise HTTPException(status_code=404, detail="Board not found")
    return col


@app.delete("/api/columns/{column_id}")
def api_delete_column(column_id: int, user_id: int = Depends(get_user_id)):
    if not delete_column(column_id, user_id):
        raise HTTPException(status_code=404, detail="Column not found")
    return {"ok": True}


# --- Card CRUD ---

class CreateCardRequest(BaseModel):
    column_id: int
    title: str
    details: str = ""
    label: str = ""
    due_date: str | None = None


@app.post("/api/cards")
def api_create_card(req: CreateCardRequest, user_id: int = Depends(get_user_id)):
    card = create_card(req.column_id, req.title, req.details, user_id, req.label, req.due_date)
    if not card:
        raise HTTPException(status_code=404, detail="Column not found")
    return card


class UpdateCardRequest(BaseModel):
    title: str | None = None
    details: str | None = None
    label: str | None = None
    due_date: str | None = "UNSET"


@app.put("/api/cards/{card_id}")
def api_update_card(card_id: int, req: UpdateCardRequest, user_id: int = Depends(get_user_id)):
    if not update_card(card_id, req.title, req.details, user_id, req.label, req.due_date):
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


# --- Search ---

class SearchRequest(BaseModel):
    query: str
    board_id: int | None = None


@app.post("/api/search")
def api_search(req: SearchRequest, user_id: int = Depends(get_user_id)):
    return search_cards(user_id, req.query, req.board_id)


# --- User profile ---

class UpdateProfileRequest(BaseModel):
    display_name: str | None = None


@app.put("/api/profile")
def api_update_profile(req: UpdateProfileRequest, user_id: int = Depends(get_user_id)):
    update_user_profile(user_id, req.display_name)
    return {"ok": True}


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@app.put("/api/profile/password")
def api_change_password(req: ChangePasswordRequest, user_id: int = Depends(get_user_id)):
    if len(req.new_password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    if not change_password(user_id, req.old_password, req.new_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    return {"ok": True}


# --- AI Chat ---

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    board_id: int | None = None


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

    if req.board_id:
        board = get_board(req.board_id, user_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
    else:
        board = get_default_board(user_id)

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

    if req.board_id:
        updated_board = get_board(req.board_id, user_id)
    else:
        updated_board = get_default_board(user_id)

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
