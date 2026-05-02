from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import authenticate_user, create_access_token, get_current_user
from app.core.config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    expires_in: int


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(payload: LoginRequest):
    if not authenticate_user(payload.username, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(payload.username, expires)
    return LoginResponse(
        access_token=token,
        username=payload.username,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", summary="获取当前登录用户")
async def current_user(username: str = Depends(get_current_user)):
    return {"username": username}
