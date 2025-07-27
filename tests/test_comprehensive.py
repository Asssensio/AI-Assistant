# путь: tests/test_comprehensive.py
"""
Комплексные тесты для всех компонентов AI Assistant.
"""

import pytest
import asyncio
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Backend tests
@pytest.mark.asyncio
async def test_database_initialization():
    """Тест инициализации базы данных."""
    from backend.app.models.database import create_tables, Base, engine
    
    # Создаем тестовую БД в памяти
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    
    # Проверяем, что таблицы созданы
    table_names = Base.metadata.tables.keys()
    assert "days" in table_names
    assert "fragments" in table_names


@pytest.mark.asyncio
async def test_day_model_properties():
    """Тест свойств модели Day."""
    from backend.app.models.day import Day
    
    day = Day(
        date=date(2024, 1, 1),
        total_fragments=5,
        total_duration_seconds=3600,
        short_summary="Test summary",
        medium_summary="Test medium summary"
    )
    
    assert day.total_duration_minutes == 60.0
    assert day.has_short_summary is True
    assert day.has_medium_summary is True
    

@pytest.mark.asyncio
async def test_fragment_model_properties():
    """Тест свойств модели Fragment."""
    from backend.app.models.fragment import Fragment
    
    fragment = Fragment(
        file_path="/test/path.wav",
        original_filename="test.wav",
        duration_seconds=600,
        start_time=datetime.now(),
        whisper_segments=[
            {"start": 0, "end": 10, "text": "Hello"},
            {"start": 10, "end": 20, "text": "World"}
        ]
    )
    
    assert fragment.duration_minutes == 10.0
    assert fragment.is_ready_for_processing is True
    
    timestamps = fragment.get_whisper_timestamps()
    assert len(timestamps) == 2
    assert timestamps[0]["text"] == "Hello"


@pytest.mark.asyncio
async def test_days_api_endpoints():
    """Тест API эндпоинтов для дней."""
    from httpx import AsyncClient
    from backend.app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Тест получения списка дней
        response = await ac.get("/days/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Тест создания дня
        response = await ac.post("/days/?day_date=2024-01-01")
        assert response.status_code in [200, 409]  # 409 если день уже существует


@pytest.mark.asyncio
async def test_fragments_api_endpoints():
    """Тест API эндпоинтов для фрагментов."""
    from httpx import AsyncClient
    from backend.app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Тест получения списка фрагментов
        response = await ac.get("/fragments/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # Тест фильтрации по дате
        response = await ac.get("/fragments/?day_date=2024-01-01")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_whisper_processor_initialization():
    """Тест инициализации Whisper процессора."""
    from backend.app.core.whisper_processor import WhisperProcessor
    
    processor = WhisperProcessor()
    
    # В мок-режиме должен сразу быть готов
    with patch.dict('os.environ', {'MOCK_WHISPER': 'true'}):
        await processor.initialize()
        
        result = await processor.transcribe_file("/fake/path.wav")
        assert result is not None
        assert "text" in result
        assert result["model"] == "mock"


@pytest.mark.asyncio
async def test_whisper_processor_batch():
    """Тест пакетной обработки Whisper."""
    from backend.app.core.whisper_processor import WhisperProcessor
    
    processor = WhisperProcessor()
    
    with patch.dict('os.environ', {'MOCK_WHISPER': 'true'}):
        files = ["/fake/file1.wav", "/fake/file2.wav"]
        results = await processor.transcribe_batch(files)
        
        assert len(results) == 2
        assert all(result is not None for result in results.values())


@pytest.mark.asyncio
async def test_file_watcher_initialization():
    """Тест инициализации file watcher."""
    from backend.app.core.file_watcher import FileWatcher
    
    watcher = FileWatcher()
    assert watcher.is_running is False
    
    # Тест запуска
    await watcher.start()
    assert watcher.is_running is True
    
    # Тест статистики
    stats = watcher.get_stats()
    assert "is_running" in stats
    assert "pending_files" in stats
    
    await watcher.stop()


@pytest.mark.asyncio
async def test_file_watcher_date_extraction():
    """Тест извлечения даты из пути файла."""
    from backend.app.core.file_watcher import FileWatcher
    from pathlib import Path
    
    watcher = FileWatcher()
    
    # Тест корректного пути
    path1 = Path("/recordings/2024-01-01/2024-01-01_10-30-00.wav")
    date_str = watcher.extract_date_from_path(path1)
    assert date_str == "2024-01-01"
    
    # Тест некорректного пути
    path2 = Path("/recordings/invalid/file.wav")
    date_str = watcher.extract_date_from_path(path2)
    assert date_str is None


# Raspberry Pi tests
def test_pi_audio_config():
    """Тест Pi-специфичной конфигурации."""
    try:
        from raspberry_pi.config import get_pi_audio_config
        config = get_pi_audio_config()
        
        assert "sample_rate" in config
        assert "channels" in config
        assert "base_path" in config
        assert config["sample_rate"] == 16000
    except ImportError:
        # Fallback тест
        from libs.config import get_audio_config
        config = get_audio_config()
        assert "sample_rate" in config


def test_pi_transfer_config():
    """Тест конфигурации передачи файлов Pi."""
    try:
        from raspberry_pi.config import get_pi_transfer_config
        config = get_pi_transfer_config()
        
        assert "pc_host" in config
        assert "pc_user" in config
        assert "verification_enabled" in config
    except ImportError:
        # Fallback тест
        from libs.config import get_transfer_config
        config = get_transfer_config()
        assert "remote_host" in config


@pytest.mark.asyncio
async def test_audio_recorder_mock_mode():
    """Тест мок-режима аудио рекордера."""
    from raspberry_pi.audio_recorder import AudioRecorder
    from datetime import datetime
    
    with patch('raspberry_pi.audio_recorder.pyaudio', None):
        recorder = AudioRecorder()
        
        # В мок-режиме должен создать файл
        with patch.object(Path, 'touch') as mock_touch:
            result_path = recorder.record_chunk(1)  # 1 минута
            mock_touch.assert_called_once()
            assert str(result_path).endswith('.wav')


def test_file_sender_retry_mechanism():
    """Тест механизма повторных попыток в file_sender."""
    from raspberry_pi.file_sender import FileSender
    from pathlib import Path
    
    sender = FileSender()
    
    # Мокаем конфигурацию для быстрых тестов
    sender.system_config = {
        "max_retries": 2,
        "retry_delay": 0.1
    }
    
    test_file = Path("/fake/test.wav")
    
    with patch('subprocess.run') as mock_run:
        # Настраиваем неудачные попытки
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Connection failed"
        
        result = sender.send_file(test_file)
        assert result is False
        assert mock_run.call_count >= 2  # Проверяем повторные попытки


# Integration tests
@pytest.mark.asyncio
async def test_full_pipeline_mock():
    """Интеграционный тест полного пайплайна обработки."""
    from backend.app.core.file_watcher import FileWatcher
    from backend.app.models.database import get_db_sync
    from backend.app.models.day import Day
    from pathlib import Path
    
    # Создаем мок-файл
    test_file = Path("/fake/recordings/2024-01-01/2024-01-01_10-00-00.wav")
    
    with patch.dict('os.environ', {'MOCK_WHISPER': 'true'}):
        watcher = FileWatcher()
        
        # Мокаем проверку готовности файла
        with patch.object(watcher, 'is_file_ready', return_value=True):
            with patch.object(Path, 'stat') as mock_stat:
                mock_stat.return_value.st_size = 1000
                
                # Мокаем добавление в БД
                with patch.object(watcher, 'add_file_to_database') as mock_add:
                    mock_fragment = MagicMock()
                    mock_fragment.id = 1
                    mock_fragment.original_filename = "test.wav"
                    mock_add.return_value = mock_fragment
                    
                    await watcher.process_audio_file(str(test_file))
                    
                    # Проверяем, что файл был обработан
                    mock_add.assert_called_once()


@pytest.mark.asyncio 
async def test_api_error_handling():
    """Тест обработки ошибок в API."""
    from httpx import AsyncClient
    from backend.app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Тест некорректной даты
        response = await ac.get("/days/invalid-date")
        assert response.status_code == 400
        
        # Тест несуществующего фрагмента
        response = await ac.get("/fragments/99999")
        assert response.status_code == 404


# Performance tests
@pytest.mark.asyncio
async def test_database_performance():
    """Тест производительности операций с БД."""
    import time
    from backend.app.models.database import get_db_sync
    from backend.app.models.day import Day
    from backend.app.models.fragment import Fragment
    
    db = get_db_sync()
    
    try:
        # Создаем тестовые данные
        test_day = Day(date=date(2024, 1, 1))
        db.add(test_day)
        db.commit()
        
        # Измеряем время создания фрагментов
        start_time = time.time()
        
        for i in range(10):
            fragment = Fragment(
                day_id=test_day.id,
                file_path=f"/test/fragment_{i}.wav",
                original_filename=f"fragment_{i}.wav",
                start_time=datetime.now()
            )
            db.add(fragment)
        
        db.commit()
        end_time = time.time()
        
        # Проверяем, что операции выполняются быстро
        assert (end_time - start_time) < 1.0  # Менее 1 секунды
        
    finally:
        db.close()


# Configuration tests
def test_config_validation():
    """Тест валидации конфигурации."""
    from libs.config import validate_config
    
    with patch.dict('os.environ', {
        'OPENAI_API_KEY': 'test-key',
        'TELEGRAM_BOT_TOKEN': 'test-token',
        'SECRET_KEY': 'production-secret'
    }):
        assert validate_config() is True


def test_env_loading():
    """Тест загрузки переменных окружения."""
    from libs.config import get_app_config, get_whisper_config
    
    with patch.dict('os.environ', {
        'DEBUG': 'false',
        'BACKEND_PORT': '9000',
        'WHISPER_MODEL': 'base'
    }):
        app_config = get_app_config()
        whisper_config = get_whisper_config()
        
        assert app_config["debug"] is False
        assert app_config["port"] == 9000
        assert whisper_config["model"] == "base" 