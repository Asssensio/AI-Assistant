"""
Настройка базы данных и ORM моделей.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from libs.config import get_database_config

# Базовый класс для всех моделей
Base = declarative_base()

# Конфигурация
db_config = get_database_config()

# Создание движка базы данных
engine = create_engine(
    db_config["url"],
    echo=db_config["echo"],
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in db_config["url"] else {}
)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def create_tables():
    """Создание всех таблиц базы данных."""
    print("🗄️ Инициализация базы данных...")
    
    # Импортируем все модели чтобы они были зарегистрированы
    from .day import Day
    from .fragment import Fragment
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")


def get_db() -> Generator[Session, None, None]:
    """Dependency для получения сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_sync() -> Session:
    """Синхронное получение сессии базы данных."""
    return SessionLocal()


async def init_db():
    """Инициализация базы данных с созданием таблиц."""
    await create_tables()


async def close_db():
    """Закрытие соединений с базой данных."""
    engine.dispose()
    print("✅ Соединения с БД закрыты") 