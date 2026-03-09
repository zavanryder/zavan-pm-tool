from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth import router as auth_router, get_current_user, USERS
from database import init_db, ensure_user, get_board, rename_column, create_card, update_card, delete_card, move_card


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    for username, password in USERS.items():
        ensure_user(username, password)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)

STATIC_DIR = Path(__file__).parent / "static"


def get_user_id(username: str = Depends(get_current_user)) -> int:
    return ensure_user(username, USERS[username])


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
    if not move_card(card_id, req.target_column_id, req.position, user_id):
        raise HTTPException(status_code=404, detail="Card or column not found")
    return {"ok": True}


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[dict] = []


@app.post("/api/ai/chat")
def ai_chat(req: ChatRequest, user_id: int = Depends(get_user_id)):
    from ai import chat, build_messages, parse_response

    board = get_board(user_id)
    messages = build_messages(board, req.message, req.conversation_history)
    raw = chat(messages)
    result = parse_response(raw)

    for update in result.get("board_updates", []):
        action = update.get("action")
        if action == "add_card":
            create_card(update["column_id"], update["title"], update.get("details", ""), user_id)
        elif action == "update_card":
            update_card(update["card_id"], update.get("title"), update.get("details"), user_id)
        elif action == "move_card":
            move_card(update["card_id"], update["target_column_id"], update.get("position", 0), user_id)
        elif action == "delete_card":
            delete_card(update["card_id"], user_id)

    updated_board = get_board(user_id)
    return {"message": result["message"], "board_updates": result["board_updates"], "board": updated_board}


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
