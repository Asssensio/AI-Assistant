# путь: tests/test_integration_backend.py
"""
Интеграционные тесты для Backend Core Logic через FastAPI.
"""

import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
from datetime import datetime, date
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_full_pipeline_integration():
    """Полный интеграционный тест: файл → FileWatcher → Whisper → Database → API."""
    from backend.app.main import app
    from backend.app.core.file_watcher import FileWatcher
    from backend.app.models.day import Day
    from backend.app.models.fragment import Fragment
    
    # Создаем временный аудиофайл
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_file.write(b"fake audio data for testing")
        temp_path = Path(temp_file.name)
    
    try:
        # Мокаем Whisper результат
        mock_whisper_result = {
            "text": "Это тестовая транскрипция аудиофайла",
            "segments": [
                {"start": 0.0, "end": 3.0, "text": "Это тестовая"},
                {"start": 3.0, "end": 6.0, "text": "транскрипция аудиофайла"}
            ],
            "language": "ru",
            "duration": 6.0,
            "model": "large-v3"
        }
        
        # Создаем FileWatcher с мокнутым Whisper
        watcher = FileWatcher()
        
        with patch.object(watcher, 'whisper_processor') as mock_processor:
            mock_processor.transcribe_file = AsyncMock(return_value=mock_whisper_result)
            
            # Мокаем database операции
            with patch('backend.app.core.file_watcher.get_db_sync') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                
                # Мокаем Day
                mock_day = MagicMock(spec=Day)
                mock_day.id = 1
                mock_day.date = date.today()
                mock_day.total_fragments = 0
                mock_day.total_duration_seconds = 0.0
                
                # Мокаем Fragment
                mock_fragment = MagicMock(spec=Fragment)
                mock_fragment.id = 1
                mock_fragment.day_id = 1
                mock_fragment.original_filename = temp_path.name
                mock_fragment.file_path = str(temp_path)
                
                mock_session.query.return_value.filter.return_value.first.side_effect = [
                    mock_day,  # Поиск дня
                    None,      # Проверка существующего фрагмента
                    mock_fragment,  # Для транскрипции
                    mock_day   # Для обновления дня
                ]
                
                # Мокаем extract методы
                with patch.object(watcher, 'extract_date_from_path', return_value='2024-01-01'):
                    with patch.object(watcher, 'extract_start_time_from_filename', return_value=datetime.now()):
                        
                        # 1. Добавляем файл в базу
                        fragment = await watcher.add_file_to_database(temp_path)
                        assert fragment is not None
                        
                        # 2. Транскрибируем фрагмент
                        await watcher.transcribe_fragment(mock_fragment)
                        
                        # Проверяем что Whisper был вызван
                        mock_processor.transcribe_file.assert_called_once_with(str(temp_path))
                        
                        # Проверяем что результат сохранился
                        assert mock_fragment.transcript_text == "Это тестовая транскрипция аудиофайла"
                        assert mock_fragment.transcribed is True
                        assert mock_fragment.whisper_model_used == "large-v3"
                        
                        # 3. Тестируем API доступ к результатам
                        with patch('backend.app.api.fragments.get_db') as mock_api_db:
                            mock_api_session = MagicMock()
                            mock_api_db.return_value.__enter__.return_value = mock_api_session
                            mock_api_session.query.return_value.filter.return_value.first.return_value = mock_fragment
                            
                            async with AsyncClient(app=app, base_url="http://test") as ac:
                                response = await ac.get("/fragments/1")
                                assert response.status_code == 200
                                data = response.json()
                                assert data["transcript_text"] == "Это тестовая транскрипция аудиофайла"
    
    finally:
        # Удаляем временный файл
        import os
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_file_watcher_stats_endpoint():
    """Тест получения статистики FileWatcher через API."""
    from backend.app.main import app
    
    # Мокаем file_watcher в main
    with patch('backend.app.main.file_watcher') as mock_watcher:
        mock_watcher.get_stats.return_value = {
            "is_running": True,
            "pending_files": 5,
            "processing_tasks": 2,
            "processed_files": 100,
            "recordings_path": "/test/recordings"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/stats")
            assert response.status_code == 200
            
            data = response.json()
            assert data["file_watcher"]["is_running"] is True
            assert data["file_watcher"]["pending_files"] == 5
            assert data["file_watcher"]["processing_tasks"] == 2


@pytest.mark.asyncio
async def test_whisper_processor_performance():
    """Тест производительности WhisperProcessor."""
    from backend.app.core.whisper_processor import WhisperProcessor
    import time
    
    processor = WhisperProcessor()
    
    # Мокаем модель для измерения времени
    with patch.object(processor, 'is_initialized', True):
        with patch.object(processor, 'model', MagicMock()):
            mock_result = {
                "text": "Быстрая транскрипция",
                "segments": [],
                "language": "ru"
            }
            
            async def mock_transcribe(*args, **kwargs):
                await asyncio.sleep(0.1)  # Имитация обработки
                return mock_result
            
            processor.model.transcribe = MagicMock(return_value=mock_result)
            
            # Измеряем время транскрипции
            start_time = time.time()
            result = await processor.transcribe_file("/fake/path.wav")
            end_time = time.time()
            
            assert result is not None
            assert result["text"] == "Быстрая транскрипция"
            
            # Проверяем что обработка заняла разумное время
            processing_time = end_time - start_time
            assert processing_time < 2.0  # Должно быть быстро для мока


@pytest.mark.asyncio
async def test_error_recovery_scenarios():
    """Тест сценариев восстановления после ошибок."""
    from backend.app.core.file_watcher import FileWatcher
    from backend.app.models.fragment import Fragment
    
    watcher = FileWatcher()
    
    # Тест 1: Ошибка соединения с базой
    mock_fragment = MagicMock(spec=Fragment)
    mock_fragment.id = 1
    mock_fragment.original_filename = "test.wav"
    
    with patch.object(watcher, 'general_config', {'max_retries': 2, 'retry_delay': 0.01}):
        with patch.object(watcher, 'whisper_processor') as mock_processor:
            mock_processor.transcribe_file = AsyncMock(return_value={"text": "Success", "segments": []})
            
            # Мокаем database ошибку
            with patch('backend.app.core.file_watcher.get_db_sync', side_effect=Exception("DB Connection Failed")):
                await watcher.transcribe_fragment(mock_fragment)
                # Должно обработать ошибку gracefully
    
    # Тест 2: Ошибка Whisper процессора
    with patch.object(watcher, 'general_config', {'max_retries': 2, 'retry_delay': 0.01}):
        with patch.object(watcher, 'whisper_processor') as mock_processor:
            mock_processor.transcribe_file = AsyncMock(side_effect=Exception("Whisper Failed"))
            
            with patch('backend.app.core.file_watcher.get_db_sync') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                mock_db_fragment = MagicMock()
                mock_session.query.return_value.filter.return_value.first.return_value = mock_db_fragment
                
                await watcher.transcribe_fragment(mock_fragment)
                
                # Проверяем что ошибка записалась в базу
                assert "Все 2 попыток неудачны" in mock_db_fragment.processing_error
                assert mock_db_fragment.retry_count == 2


@pytest.mark.asyncio 
async def test_concurrent_processing():
    """Тест одновременной обработки нескольких файлов."""
    from backend.app.core.file_watcher import FileWatcher
    
    watcher = FileWatcher()
    watcher.is_running = True
    
    # Добавляем несколько файлов в очередь
    test_files = [f"/test/file{i}.wav" for i in range(5)]
    for file_path in test_files:
        watcher.pending_files.add(file_path)
    
    processed_files = []
    
    async def mock_process_file(file_path):
        await asyncio.sleep(0.1)  # Имитация обработки
        processed_files.append(file_path)
    
    with patch.object(watcher, 'process_audio_file', side_effect=mock_process_file):
        # Запускаем один цикл обработки
        with patch.object(watcher, 'is_running', side_effect=[True, False]):
            await watcher.processing_loop()
    
    # Проверяем что все файлы были отправлены на обработку
    assert len(watcher.processing_tasks) == 5
    
    # Ждем завершения всех задач
    if watcher.processing_tasks:
        await asyncio.gather(*watcher.processing_tasks.values())
    
    assert len(processed_files) == 5
    assert all(f in processed_files for f in test_files)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 