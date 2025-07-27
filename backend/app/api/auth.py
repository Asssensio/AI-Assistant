"""
Аутентификация и авторизация API.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    """Модель запроса логина."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Модель ответа с токеном."""
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Аутентификация пользователя."""
    # TODO: Реализовать реальную аутентификацию
    if request.username == "admin" and request.password == "admin":
        return TokenResponse(access_token="mock-jwt-token")
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me")
async def get_current_user():
    """Получение информации о текущем пользователе."""
    # TODO: Реализовать получение пользователя из JWT
    return {"username": "admin", "role": "admin"} 