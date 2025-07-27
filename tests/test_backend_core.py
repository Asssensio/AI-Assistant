# путь: tests/test_backend_core.py
"""
Тесты для Backend Core Logic - WhisperProcessor и FileWatcher.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from datetime import datetime, date
import tempfile
import os

@pytest.mark.asyncio
async def test_whisper_processor_timeout():
    """Тест timeout функциональности WhisperProcessor."""
    from backend.app.core.whisper_processor import WhisperProcessor
    
    processor = WhisperProcessor()
    
    # Мокаем конфигурацию с коротким timeout
    with patch.object(processor, 'config', {'timeout': 1, 'model': 'base'}):
        with patch.object(processor, 'model', MagicMock()):
            with patch('backend.app.core.whisper_processor.platform.system', return_value='Linux'):
                with patch.object(processor.model, 'transcribe', side_effect=lambda *args, **kwargs: asyncio.sleep(5)):
                    # Timeout должен сработать
                    result = await processor.transcribe_file("/fake/path.wav")
                    assert result is None


@pytest.mark.asyncio
async def test_whisper_processor_enhanced_options():
    """Тест улучшенных опций Whisper."""
    from backend.app.core.whisper_processor import WhisperProcessor
    
    processor = WhisperProcessor()
    mock_result = {
        "text": "Тестовый текст",
        "segments": [{"start": 0, "end": 5, "text": "Тестовый текст"}],
        "language": "ru"
    }
    
    with patch.object(processor, 'config', {
        'model': 'base', 
        'language': 'ru', 
        'task': 'transcribe',
        'compute_type': 'float16',
        'timeout': 300
    }):
        with patch.object(processor, 'model', MagicMock()):
            with patch.object(processor.model, 'transcribe', return_value=mock_result) as mock_transcribe:
                with patch.object(processor, 'is_initialized', True):
                    result = await processor.transcribe_file("/fake/path.wav")
                    
                    # Проверяем что вызвался с правильными опциями
                    mock_transcribe.assert_called_once()
                    call_kwargs = mock_transcribe.call_args[1]
                    
                    assert call_kwargs['language'] == 'ru'
                    assert call_kwargs['task'] == 'transcribe'
                    assert call_kwargs['fp16'] is True
                    assert call_kwargs['temperature'] == 0.0
                    assert call_kwargs['compression_ratio_threshold'] == 2.4
                    assert call_kwargs['logprob_threshold'] == -1.0
                    assert call_kwargs['no_speech_threshold'] == 0.6


@pytest.mark.asyncio
async def test_file_watcher_retry_mechanism():
    """Тест retry механизма FileWatcher."""
    from backend.app.core.file_watcher import FileWatcher
    from backend.app.models.fragment import Fragment
    
    watcher = FileWatcher()
    
    # Мокаем конфигурацию
    with patch.object(watcher, 'general_config', {'max_retries': 3, 'retry_delay': 0.1}):
        # Создаем мок фрагмент
        mock_fragment = MagicMock(spec=Fragment)
        mock_fragment.id = 1
        mock_fragment.original_filename = "test.wav"
        
        # Мокаем WhisperProcessor чтобы он падал первые 2 раза
        call_count = 0
        async def mock_transcribe(file_path):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary error")
            return {"text": "Success", "segments": [], "model": "test"}
        
        with patch.object(watcher, 'whisper_processor', MagicMock()):
            watcher.whisper_processor.transcribe_file = mock_transcribe
            
            with patch('backend.app.core.file_watcher.get_db_sync') as mock_db:
                mock_session = MagicMock()
                mock_db.return_value = mock_session
                mock_db_fragment = MagicMock()
                mock_session.query.return_value.filter.return_value.first.return_value = mock_db_fragment
                
                # Запускаем транскрипцию
                await watcher.transcribe_fragment(mock_fragment)
                
                # Проверяем что было 3 попытки
                assert call_count == 3
                # Проверяем что результат сохранился
                assert mock_db_fragment.transcript_text == "Success"
                assert mock_db_fragment.transcribed is True


@pytest.mark.asyncio
async def test_file_watcher_adaptive_sleep():
    """Тест адаптивного интервала проверки FileWatcher."""
    from backend.app.core.file_watcher import FileWatcher
    
    watcher = FileWatcher()
    watcher.is_running = True
    watcher.pending_files = set()
    
    # Мокаем tasks для разного количества
    with patch.object(watcher, 'processing_tasks', {}):  # Мало задач
        with patch('asyncio.sleep') as mock_sleep:
            with patch.object(watcher, 'is_running', side_effect=[True, False]):  # Один цикл
                await watcher.processing_loop()
                mock_sleep.assert_called_with(5)  # Быстрый интервал
    
    with patch.object(watcher, 'processing_tasks', {f'task{i}': MagicMock() for i in range(5)}):  # Много задач
        with patch('asyncio.sleep') as mock_sleep:
            with patch.object(watcher, 'is_running', side_effect=[True, False]):  # Один цикл
                await watcher.processing_loop()
                mock_sleep.assert_called_with(10)  # Медленный интервал


@pytest.mark.asyncio
async def test_file_watcher_database_integration():
    """Тест интеграции FileWatcher с базой данных."""
    from backend.app.core.file_watcher import FileWatcher
    from backend.app.models.day import Day
    from backend.app.models.fragment import Fragment
    
    watcher = FileWatcher()
    
    # Создаем временный файл
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_file.write(b"fake audio data")
        temp_path = Path(temp_file.name)
    
    try:
        # Мокаем database операции
        with patch('backend.app.core.file_watcher.get_db_sync') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            
            # Мокаем Day и Fragment
            mock_day = MagicMock(spec=Day)
            mock_day.id = 1
            mock_session.query.return_value.filter.return_value.first.side_effect = [
                mock_day,  # Для поиска дня
                None       # Для проверки существующего фрагмента
            ]
            
            # Мокаем extract методы
            with patch.object(watcher, 'extract_date_from_path', return_value='2024-01-01'):
                with patch.object(watcher, 'extract_start_time_from_filename', return_value=datetime.now()):
                    
                    fragment = await watcher.add_file_to_database(temp_path)
                    
                    # Проверяем что фрагмент был создан
                    assert mock_session.add.called
                    assert mock_session.commit.called
                    
                    # Проверяем что статистика дня обновилась
                    assert mock_day.total_fragments == 1
    
    finally:
        # Удаляем временный файл
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_whisper_config_validation():
    """Тест валидации конфигурации Whisper."""
    from libs.config import get_whisper_config
    
    # Тест дефолтных значений
    with patch.dict('os.environ', {}, clear=True):
        config = get_whisper_config()
        assert config['model'] == 'large-v3'
        assert config['timeout'] == 300
        assert config['max_retries'] == 3
        assert config['retry_delay'] == 30
    
    # Тест кастомных значений
    with patch.dict('os.environ', {
        'WHISPER_MODEL': 'base',
        'WHISPER_TIMEOUT': '600',
        'WHISPER_MAX_RETRIES': '5'
    }):
        config = get_whisper_config()
        assert config['model'] == 'base'
        assert config['timeout'] == 600
        assert config['max_retries'] == 5


@pytest.mark.asyncio
async def test_whisper_processor_memory_management():
    """Тест управления памятью WhisperProcessor."""
    from backend.app.core.whisper_processor import WhisperProcessor
    
    processor = WhisperProcessor()
    
    # Мокаем torch и модель
    with patch('backend.app.core.whisper_processor.torch') as mock_torch:
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.empty_cache = MagicMock()
        
        processor.model = MagicMock()
        processor.is_initialized = True
        
        # Тестируем cleanup
        await processor.cleanup()
        
        assert processor.model is None
        assert processor.is_initialized is False
        mock_torch.cuda.empty_cache.assert_called_once()


def test_file_path_extraction():
    """Тест извлечения даты и времени из путей файлов."""
    from backend.app.core.file_watcher import FileWatcher
    
    watcher = FileWatcher()
    
    # Тест извлечения даты из пути
    test_path = Path("/recordings/2024-01-15/audio.wav")
    date_str = watcher.extract_date_from_path(test_path)
    assert date_str == "2024-01-15"
    
    # Тест неправильного пути
    bad_path = Path("/recordings/invalid/audio.wav")
    date_str = watcher.extract_date_from_path(bad_path)
    assert date_str is None
    
    # Тест извлечения времени из имени файла
    test_date = date(2024, 1, 15)
    filename = "2024-01-15_14-30-00.wav"
    start_time = watcher.extract_start_time_from_filename(filename, test_date)
    
    assert start_time.date() == test_date
    assert start_time.hour == 14
    assert start_time.minute == 30
    assert start_time.second == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 