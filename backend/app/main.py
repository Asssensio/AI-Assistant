"""
FastAPI Backend для AI Assistant.

Основное приложение для обработки аудио, управления базой данных 
и предоставления API для веб-интерфейса.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from libs.config import get_app_config, get_cors_config
from backend.app.api import auth, days, fragments
from backend.app.models.database import create_tables
from backend.app.core.file_watcher import FileWatcher


# Глобальная переменная для file watcher
file_watcher: FileWatcher = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Управление жизненным циклом приложения."""
    # Startup
    print("🚀 Запуск AI Assistant Backend...")
    
    # Инициализация базы данных
    await create_tables()
    print("✅ База данных инициализирована")
    
    # Запуск мониторинга файлов
    global file_watcher
    file_watcher = FileWatcher()
    await file_watcher.start()
    print("✅ Мониторинг файлов запущен")
    
    yield
    
    # Shutdown
    print("🛑 Завершение работы AI Assistant Backend...")
    if file_watcher:
        await file_watcher.stop()
        print("✅ Мониторинг файлов остановлен")


# Конфигурация
app_config = get_app_config()
cors_config = get_cors_config()

# Создание FastAPI приложения
app = FastAPI(
    title="AI Assistant API",
    description="Personal Voice Recording and Analysis System API",
    version="0.1.0",
    docs_url="/docs" if app_config["debug"] else None,
    redoc_url="/redoc" if app_config["debug"] else None,
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["origins"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=app_config["allowed_hosts"]
)


# Обработчики ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Обработчик HTTP исключений."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Обработчик общих исключений."""
    if app_config["debug"]:
        import traceback
        error_detail = traceback.format_exc()
    else:
        error_detail = "Internal server error"
        
    return JSONResponse(
        status_code=500,
        content={
            "error": error_detail,
            "status_code": 500
        }
    )


# Основные маршруты
@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "🎙️ AI Assistant API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка состояния сервиса."""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: реальная проверка БД
        "file_watcher": "running" if file_watcher and file_watcher.is_running else "stopped"
    }


@app.get("/stats")
async def get_stats():
    """Получение базовой статистики."""
    # TODO: Реализовать получение статистики из БД
    return {
        "total_days": 0,
        "total_fragments": 0,
        "total_duration_hours": 0,
        "last_recording": None
    }


# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(days.router, prefix="/days", tags=["days"])
app.include_router(fragments.router, prefix="/fragments", tags=["fragments"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=app_config["host"],
        port=app_config["port"],
        reload=app_config["debug"],
        log_level="info"
    ) 