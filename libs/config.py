# путь: libs/config.py
"""
Конфигурация для всех компонентов AI Assistant.

Читает настройки из переменных окружения и предоставляет 
типизированные конфигурации для разных компонентов.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()


def get_bool_env(key: str, default: bool = False) -> bool:
    """Получение boolean значения из переменной окружения."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_int_env(key: str, default: int = 0) -> int:
    """Получение integer значения из переменной окружения."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_list_env(key: str, default: Optional[List[str]] = None) -> List[str]:
    """Получение списка из переменной окружения (разделитель - запятая)."""
    if default is None:
        default = []
    value = os.getenv(key, "")
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


# === ОБЩИЕ НАСТРОЙКИ ===

def get_general_config() -> Dict[str, Any]:
    """Общие настройки системы."""
    return {
        "debug": get_bool_env("DEBUG", True),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "timezone": os.getenv("TIMEZONE", "Europe/Moscow"),
    }


# === БАЗА ДАННЫХ ===

def get_database_config() -> Dict[str, Any]:
    """Конфигурация базы данных."""
    return {
        "url": os.getenv("DATABASE_URL", "sqlite:///./ai_assistant.db"),
        "echo": get_bool_env("DB_ECHO", False),
        "pool_size": get_int_env("DB_POOL_SIZE", 5),
        "max_overflow": get_int_env("DB_MAX_OVERFLOW", 10),
    }


# === BACKEND API ===

def get_app_config() -> Dict[str, Any]:
    """Конфигурация FastAPI приложения."""
    return {
        "host": os.getenv("BACKEND_HOST", "localhost"),
        "port": get_int_env("BACKEND_PORT", 8000),
        "debug": get_bool_env("DEBUG", True),
        "secret_key": os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production"),
        "algorithm": os.getenv("ALGORITHM", "HS256"),
        "access_token_expire_days": get_int_env("ACCESS_TOKEN_EXPIRE_DAYS", 30),
        "allowed_hosts": get_list_env("ALLOWED_HOSTS", ["localhost", "127.0.0.1"]),
    }


def get_cors_config() -> Dict[str, Any]:
    """Конфигурация CORS."""
    return {
        "origins": get_list_env("CORS_ORIGINS", ["http://localhost:3000", "http://127.0.0.1:3000"]),
    }


# === WHISPER ===

def get_whisper_config() -> Dict[str, Any]:
    """Конфигурация Whisper."""
    return {
        "model": os.getenv("WHISPER_MODEL", "large-v3"),
        "device": os.getenv("WHISPER_DEVICE", "cuda"),
        "compute_type": os.getenv("WHISPER_COMPUTE_TYPE", "float16"),
        "language": os.getenv("WHISPER_LANGUAGE", "ru"),
        "task": os.getenv("WHISPER_TASK", "transcribe"),
    }


# === АУДИО ===

def get_audio_config() -> Dict[str, Any]:
    """Конфигурация аудио записи."""
    return {
        "sample_rate": get_int_env("AUDIO_SAMPLE_RATE", 16000),
        "channels": get_int_env("AUDIO_CHANNELS", 1),
        "format": os.getenv("AUDIO_FORMAT", "WAV"),
        "chunk_minutes": get_int_env("RECORDING_CHUNK_MINUTES", 10),
        "base_path": os.getenv("RECORDINGS_BASE_PATH", "/recordings"),
    }


# === RASPBERRY PI ===

def get_pi_config() -> Dict[str, Any]:
    """Конфигурация Raspberry Pi."""
    return {
        "host": os.getenv("PI_HOST", "raspberrypi.local"),
        "user": os.getenv("PI_USER", "pi"),
        "ssh_key_path": os.path.expanduser(os.getenv("PI_SSH_KEY_PATH", "~/.ssh/id_rsa")),
        "recordings_path": os.getenv("PI_RECORDINGS_PATH", "/home/pi/recordings"),
    }


def get_transfer_config() -> Dict[str, Any]:
    """Конфигурация передачи файлов."""
    return {
        "source_path": os.getenv("PI_RECORDINGS_PATH", "/home/pi/recordings"),
        "remote_host": os.getenv("PI_HOST", "192.168.1.100"),
        "remote_user": os.getenv("PI_USER", "user"),
        "remote_path": os.getenv("PC_RECORDINGS_PATH", "/recordings"),
        "ssh_key_path": os.path.expanduser(os.getenv("PI_SSH_KEY_PATH", "~/.ssh/id_rsa")),
    }


# === OPENAI ===

def get_openai_config() -> Dict[str, Any]:
    """Конфигурация OpenAI API."""
    return {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
        "max_tokens": get_int_env("OPENAI_MAX_TOKENS", 4000),
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
    }


# === TELEGRAM ===

def get_telegram_config() -> Dict[str, Any]:
    """Конфигурация Telegram бота."""
    return {
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "webhook_url": os.getenv("TELEGRAM_WEBHOOK_URL", ""),
        "polling": not bool(os.getenv("TELEGRAM_WEBHOOK_URL")),
    }


# === BACKUP ===

def get_backup_config() -> Dict[str, Any]:
    """Конфигурация резервного копирования."""
    return {
        "enabled": get_bool_env("BACKUP_ENABLED", True),
        "path": os.getenv("BACKUP_PATH", "/backups"),
        "schedule": os.getenv("BACKUP_SCHEDULE", "0 2 * * *"),  # Daily at 2 AM
        "retention_days": get_int_env("BACKUP_RETENTION_DAYS", 30),
    }


# === DEVELOPMENT ===

def get_dev_config() -> Dict[str, Any]:
    """Конфигурация для разработки."""
    return {
        "dev_mode": get_bool_env("DEV_MODE", True),
        "mock_whisper": get_bool_env("MOCK_WHISPER", False),
        "mock_telegram": get_bool_env("MOCK_TELEGRAM", False),
    }


# === ПУТИ ===

def get_paths_config() -> Dict[str, Path]:
    """Конфигурация путей."""
    recordings_path = Path(os.getenv("RECORDINGS_BASE_PATH", "/recordings"))
    
    return {
        "recordings": recordings_path,
        "models": Path(os.getenv("MODELS_PATH", "./models")),
        "logs": Path(os.getenv("LOGS_PATH", "./logs")),
        "cache": Path(os.getenv("CACHE_PATH", "./.cache")),
        "backups": Path(os.getenv("BACKUP_PATH", "/backups")),
    }


# === ВАЛИДАЦИЯ КОНФИГУРАЦИИ ===

def validate_config() -> bool:
    """Проверка критически важных настроек."""
    errors = []
    
    # Проверка OpenAI API ключа
    if not get_openai_config()["api_key"]:
        errors.append("OPENAI_API_KEY не установлен")
    
    # Проверка Telegram токена
    telegram_config = get_telegram_config()
    if not telegram_config["bot_token"] and not get_dev_config()["mock_telegram"]:
        errors.append("TELEGRAM_BOT_TOKEN не установлен")
    
    # Проверка секретного ключа в production
    app_config = get_app_config()
    if not app_config["debug"] and app_config["secret_key"] == "your-secret-key-change-this-in-production":
        errors.append("SECRET_KEY должен быть изменён в production")
    
    if errors:
        print("❌ Ошибки конфигурации:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


if __name__ == "__main__":
    # Тест конфигурации
    print("🔧 Проверка конфигурации AI Assistant...")
    
    if validate_config():
        print("✅ Конфигурация корректна")
    else:
        print("❌ Найдены ошибки в конфигурации")
        exit(1) 