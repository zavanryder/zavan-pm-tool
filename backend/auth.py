import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from database import create_user, verify_user, get_user_by_id

logger = logging.getLogger(__name__)

_jwt_from_env = os.environ.get("JWT_SECRET_KEY")
if not _jwt_from_env:
    logger.warning(
        "JWT_SECRET_KEY not set -- using a random key. "
        "All sessions will be invalidated on restart."
    )
SECRET_KEY = _jwt_from_env or os.urandom(32).hex()
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

AUTH_RATE_LIMIT_WINDOW = 60
AUTH_RATE_LIMIT_MAX = 10
_auth_attempts: dict[str, list[float]] = defaultdict(list)


def _check_auth_rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    attempts = [t for t in _auth_attempts[ip] if now - t < AUTH_RATE_LIMIT_WINDOW]
    _auth_attempts[ip] = attempts
    if len(attempts) >= AUTH_RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Too many attempts, try again later")
    attempts.append(now)


router = APIRouter(prefix="/api/auth")


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""


class LoginResponse(BaseModel):
    token: str
    username: str
    user_id: int


class UserResponse(BaseModel):
    user_id: int
    username: str
    display_name: str


def create_token(user_id: int, username: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "uid": user_id, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: Annotated[str, Header()]) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload["sub"]
        user_id = payload["uid"]
    except (jwt.InvalidTokenError, KeyError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    return {"user_id": user_id, "username": username}


@router.post("/register")
def register(req: RegisterRequest, _rate=Depends(_check_auth_rate_limit)) -> LoginResponse:
    if len(req.username) < 2:
        raise HTTPException(status_code=400, detail="Username must be at least 2 characters")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    user_id = create_user(req.username, req.password, req.display_name)
    if user_id is None:
        raise HTTPException(status_code=409, detail="Username already taken")
    token = create_token(user_id, req.username)
    return LoginResponse(token=token, username=req.username, user_id=user_id)


@router.post("/login")
def login(req: LoginRequest, _rate=Depends(_check_auth_rate_limit)) -> LoginResponse:
    user_id = verify_user(req.username, req.password)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user_id, req.username)
    return LoginResponse(token=token, username=req.username, user_id=user_id)


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    user = get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return UserResponse(
        user_id=user["id"],
        username=user["username"],
        display_name=user["display_name"],
    )
