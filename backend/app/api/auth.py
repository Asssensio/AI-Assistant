# путь: backend/app/api/auth.py
"""
Аутентификация и авторизация API.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from datetime import timedelta

from backend.app.core.auth import AuthManager, get_current_active_user

router = APIRouter()


class LoginRequest(BaseModel):
    """Модель запроса логина."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Модель ответа с токеном."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    """Информация о пользователе."""
    username: str
    role: str
    full_name: str


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Аутентификация пользователя."""
    user = AuthManager.authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем JWT токен
    access_token_expires = timedelta(minutes=30)
    access_token = AuthManager.create_access_token(
        data={"sub": user["username"], "role": user["role"], "full_name": user["full_name"]},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60  # 30 минут в секундах
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user(current_user: dict = Depends(get_current_active_user)):
    """Получение информации о текущем пользователе."""
    return UserInfo(
        username=current_user["username"],
        role=current_user["role"],
        full_name=current_user["full_name"]
    ) 