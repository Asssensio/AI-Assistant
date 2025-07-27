# путь: backend/app/core/whisper_processor.py
"""
Whisper процессор для транскрипции аудиофайлов.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import json

try:
    import whisper
    import torch
except ImportError:
    whisper = None
    torch = None

from libs.config import get_whisper_config, get_dev_config


logger = logging.getLogger(__name__)


class WhisperProcessor:
    """Процессор для транскрипции аудио через Whisper."""
    
    def __init__(self):
        """Инициализация Whisper процессора."""
        self.config = get_whisper_config()
        self.dev_config = get_dev_config()
        self.model = None
        self.is_initialized = False
        
    async def initialize(self):
        """Инициализация Whisper модели."""
        if self.is_initialized or self.dev_config["mock_whisper"]:
            return
            
        if whisper is None:
            logger.warning("⚠️ Whisper не установлен. Работа в мок-режиме.")
            return
            
        try:
            logger.info(f"🤖 Загрузка Whisper модели: {self.config['model']}")
            
            # Проверяем доступность GPU
            device = self.config["device"]
            if device == "cuda" and not torch.cuda.is_available():
                logger.warning("⚠️ CUDA недоступна, используем CPU")
                device = "cpu"
            
            # Загружаем модель
            self.model = whisper.load_model(
                self.config["model"], 
                device=device
            )
            
            self.is_initialized = True
            logger.info(f"✅ Whisper модель загружена на {device}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки Whisper: {e}")
            self.model = None
    
    async def transcribe_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Транскрипция аудиофайла."""
        if self.dev_config["mock_whisper"]:
            return await self._mock_transcribe(file_path)
        
        if not self.is_initialized:
            await self.initialize()
            
        if self.model is None:
            return await self._mock_transcribe(file_path)
        
        try:
            logger.info(f"🎯 Начало транскрипции: {Path(file_path).name}")
            
            # Запускаем транскрипцию в отдельном потоке
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._transcribe_sync, file_path
            )
            
            if result:
                logger.info(f"✅ Транскрипция завершена: {len(result.get('text', ''))} символов")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка транскрипции {file_path}: {e}")
            return None
    
    def _transcribe_sync(self, file_path: str) -> Dict[str, Any]:
        """Синхронная транскрипция файла."""
        try:
            # Опции транскрипции
            options = {
                "language": self.config.get("language", "ru"),
                "task": self.config.get("task", "transcribe"),
                "fp16": self.config.get("compute_type") == "float16",
                "verbose": False,
                "temperature": 0.0,  # Более детерминированный результат
                "compression_ratio_threshold": 2.4,  # Фильтр повторений
                "logprob_threshold": -1.0,  # Фильтр низкоуверенных сегментов
                "no_speech_threshold": 0.6,  # Порог тишины
            }
            
            # Добавляем timeout через signal (только для Unix)
            import signal
            import platform
            
            timeout_seconds = self.config.get("timeout", 300)  # 5 минут по умолчанию
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Транскрипция превысила {timeout_seconds} секунд")
            
            # Устанавливаем timeout только на Unix системах
            if platform.system() != "Windows" and timeout_seconds > 0:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_seconds)
            
            try:
                # Выполняем транскрипцию
                result = self.model.transcribe(file_path, **options)
            finally:
                if platform.system() != "Windows" and timeout_seconds > 0:
                    signal.alarm(0)  # Отключаем timeout
            
            # Форматируем результат
            return {
                "text": result["text"].strip(),
                "segments": [
                    {
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": segment["text"].strip()
                    }
                    for segment in result.get("segments", [])
                ],
                "language": result.get("language", "unknown"),
                "duration": result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0,
                "model": self.config["model"]
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронной транскрипции: {e}")
            raise
    
    async def _mock_transcribe(self, file_path: str) -> Dict[str, Any]:
        """Мок-транскрипция для разработки."""
        await asyncio.sleep(1)  # Имитация обработки
        
        filename = Path(file_path).name
        mock_text = f"[МОК ТРАНСКРИПЦИЯ] Аудиофайл {filename} обработан в режиме разработки."
        
        return {
            "text": mock_text,
            "segments": [
                {
                    "start": 0.0,
                    "end": 10.0,
                    "text": mock_text
                }
            ],
            "language": "ru",
            "duration": 10.0,
            "model": "mock"
        }
    
    async def transcribe_batch(self, file_paths: list) -> Dict[str, Optional[Dict[str, Any]]]:
        """Пакетная транскрипция файлов."""
        results = {}
        
        for file_path in file_paths:
            try:
                result = await self.transcribe_file(file_path)
                results[file_path] = result
            except Exception as e:
                logger.error(f"❌ Ошибка пакетной транскрипции {file_path}: {e}")
                results[file_path] = None
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Информация о загруженной модели."""
        if not self.is_initialized or self.model is None:
            return {
                "model": self.config["model"],
                "loaded": False,
                "device": "unknown",
                "mock_mode": self.dev_config["mock_whisper"]
            }
        
        return {
            "model": self.config["model"],
            "loaded": True,
            "device": self.config["device"],
            "mock_mode": False,
            "language": self.config.get("language", "ru"),
            "task": self.config.get("task", "transcribe")
        }
    
    async def cleanup(self):
        """Очистка ресурсов."""
        if self.model is not None:
            del self.model
            self.model = None
            
        if torch is not None and torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        self.is_initialized = False
        logger.info("🧹 Whisper процессор очищен") 