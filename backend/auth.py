import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-insecure-jwt-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

USERS = {"user": "password"}

router = APIRouter(prefix="/api/auth")


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


class UserResponse(BaseModel):
    username: str


def create_token(username: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": username, "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: Annotated[str, Header()]) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload["sub"]
    except (jwt.InvalidTokenError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid token")
    if username not in USERS:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username


@router.post("/login")
def login(req: LoginRequest) -> LoginResponse:
    if USERS.get(req.username) != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(req.username)
    return LoginResponse(token=token, username=req.username)


@router.get("/me")
def me(username: str = Depends(get_current_user)) -> UserResponse:
    return UserResponse(username=username)
