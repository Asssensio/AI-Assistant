# путь: tests/test_basic.py
"""
Базовые тесты для AI Assistant компонентов.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Тестируем конфигурацию
def test_libs_config_import():
    """Тест импорта конфигурации."""
    from libs.config import get_app_config, get_audio_config
    
    app_config = get_app_config()
    assert "host" in app_config
    assert "port" in app_config
    
    audio_config = get_audio_config()
    assert "sample_rate" in audio_config
    assert audio_config["sample_rate"] == 16000


def test_libs_exceptions_import():
    """Тест импорта исключений."""
    from libs.exceptions import AIAssistantError, AudioRecordingError
    
    # Проверяем иерархию исключений
    assert issubclass(AudioRecordingError, AIAssistantError)


# Тестируем Raspberry Pi компоненты
def test_audio_recorder_import():
    """Тест импорта аудио рекордера."""
    from raspberry_pi.audio_recorder import AudioRecorder
    
    recorder = AudioRecorder()
    assert hasattr(recorder, 'is_recording')
    assert hasattr(recorder, 'record_chunk')


def test_file_sender_import():
    """Тест импорта file sender."""
    from raspberry_pi.file_sender import FileSender
    
    sender = FileSender()
    assert hasattr(sender, 'sent_files')
    assert hasattr(sender, 'send_file')


# Тестируем Backend компоненты  
@pytest.mark.asyncio
async def test_fastapi_app_creation():
    """Тест создания FastAPI приложения."""
    from backend.app.main import app
    
    assert app.title == "AI Assistant API"
    assert app.version == "0.1.0"


@pytest.mark.asyncio 
async def test_database_init():
    """Тест инициализации базы данных."""
    from backend.app.models.database import create_tables
    
    # Не должно вызывать исключений
    await create_tables()


def test_file_watcher_import():
    """Тест импорта file watcher."""
    from backend.app.core.file_watcher import FileWatcher
    
    watcher = FileWatcher()
    assert hasattr(watcher, 'is_running')
    assert not watcher.is_running


# Интеграционные тесты
@pytest.mark.asyncio
async def test_fastapi_health_endpoint():
    """Тест health endpoint."""
    from httpx import AsyncClient
    from backend.app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_fastapi_root_endpoint():
    """Тест корневого endpoint."""
    from httpx import AsyncClient
    from backend.app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "AI Assistant" in data["message"]


# Тест конфигурации окружения
def test_env_config_validation():
    """Тест валидации конфигурации."""
    with patch.dict('os.environ', {
        'DEBUG': 'true',
        'BACKEND_PORT': '8000', 
        'AUDIO_SAMPLE_RATE': '16000'
    }):
        from libs.config import get_app_config, get_audio_config
        
        app_config = get_app_config()
        assert app_config["debug"] is True
        assert app_config["port"] == 8000
        
        audio_config = get_audio_config()
        assert audio_config["sample_rate"] == 16000


def test_mock_audio_recording():
    """Тест мок-режима записи аудио."""
    from raspberry_pi.audio_recorder import AudioRecorder
    
    recorder = AudioRecorder()
    
    # В мок-режиме должно создать пустой файл
    with patch('raspberry_pi.audio_recorder.pyaudio', None):
        test_path = recorder._get_output_path(recorder.config["base_path"])
        # Тест структуры пути
        assert str(test_path).endswith('.wav') 