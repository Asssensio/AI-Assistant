# путь: backend/app/core/auth.py
"""
JWT аутентификация и авторизация.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.models.database import get_db
from libs.config import get_app_config

# Конфигурация
config = get_app_config()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class AuthManager:
    """Менеджер аутентификации."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Хеширование пароля."""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Создание JWT токена."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Проверка JWT токена."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[dict]:
        """Аутентификация пользователя."""
        # В продакшене здесь должна быть проверка в базе данных
        # Пока используем хардкод для демонстрации
        if username == "admin":
            # Хеш пароля "admin123" (bcrypt)
            hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQ2."
            if AuthManager.verify_password(password, hashed_password):
                return {
                    "username": username,
                    "role": "admin",
                    "full_name": "Administrator"
                }
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Получение текущего пользователя из JWT токена."""
    token = credentials.credentials
    payload = AuthManager.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # В продакшене здесь должна быть проверка пользователя в базе данных
    return {
        "username": username,
        "role": payload.get("role", "user"),
        "full_name": payload.get("full_name", "")
    }


async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Получение активного пользователя."""
    if not current_user:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 