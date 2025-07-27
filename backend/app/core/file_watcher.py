# путь: backend/app/core/file_watcher.py
"""
File Watcher для мониторинга новых аудиофайлов и автоматической обработки.
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, Set
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

from libs.config import get_paths_config, get_general_config
from backend.app.models.database import get_db_sync
from backend.app.models.day import Day
from backend.app.models.fragment import Fragment
from backend.app.core.whisper_processor import WhisperProcessor


logger = logging.getLogger(__name__)


class AudioFileHandler(FileSystemEventHandler):
    """Обработчик событий файловой системы для аудиофайлов."""
    
    def __init__(self, file_watcher: 'FileWatcher'):
        self.file_watcher = file_watcher
        
    def on_created(self, event):
        """Обработка создания файла."""
        if not event.is_directory and event.src_path.endswith('.wav'):
            self.file_watcher.add_pending_file(event.src_path)
            
    def on_moved(self, event):
        """Обработка перемещения файла."""
        if not event.is_directory and event.dest_path.endswith('.wav'):
            self.file_watcher.add_pending_file(event.dest_path)


class FileWatcher:
    """Мониторинг новых аудиофайлов и их автоматическая обработка."""
    
    def __init__(self):
        """Инициализация file watcher."""
        self.is_running = False
        self.observer = None
        self.pending_files: Set[str] = set()
        self.processed_files: Set[str] = set()
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        
        # Конфигурация
        self.paths_config = get_paths_config()
        self.general_config = get_general_config()
        
        # Whisper процессор
        self.whisper_processor = WhisperProcessor()
        
        # Рабочая директория
        self.recordings_path = self.paths_config["recordings"]
        self.ensure_directories()
        
    def ensure_directories(self):
        """Создание необходимых директорий."""
        self.recordings_path.mkdir(parents=True, exist_ok=True)
        
    async def start(self):
        """Запуск мониторинга файлов."""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info(f"📁 Запуск File Watcher для {self.recordings_path}")
        
        # Сканируем существующие файлы
        await self.scan_existing_files()
        
        # Настраиваем файловый мониторинг
        self.setup_file_monitoring()
        
        # Запускаем обработчик
        asyncio.create_task(self.processing_loop())
        
    async def stop(self):
        """Остановка мониторинга."""
        self.is_running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
        # Ждем завершения всех задач обработки
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks.values(), return_exceptions=True)
            
        logger.info("📁 File Watcher остановлен")
        
    def setup_file_monitoring(self):
        """Настройка мониторинга файловой системы."""
        if not self.recordings_path.exists():
            logger.warning(f"Директория записей не существует: {self.recordings_path}")
            return
            
        self.observer = Observer()
        event_handler = AudioFileHandler(self)
        
        self.observer.schedule(
            event_handler, 
            str(self.recordings_path), 
            recursive=True
        )
        self.observer.start()
        logger.info(f"📂 Мониторинг включен для {self.recordings_path}")
        
    async def scan_existing_files(self):
        """Сканирование существующих файлов при запуске."""
        if not self.recordings_path.exists():
            return
            
        count = 0
        for wav_file in self.recordings_path.rglob("*.wav"):
            if self.is_file_ready(wav_file):
                await self.add_file_to_database(wav_file)
                count += 1
                
        logger.info(f"📊 Обнаружено {count} существующих аудиофайлов")
        
    def add_pending_file(self, file_path: str):
        """Добавление файла в очередь обработки."""
        if file_path not in self.processed_files:
            self.pending_files.add(file_path)
            logger.info(f"➕ Добавлен файл для обработки: {Path(file_path).name}")
            
    def is_file_ready(self, file_path: Path) -> bool:
        """Проверка готовности файла к обработке."""
        try:
            # Проверяем, что файл не растет (запись завершена)
            size1 = file_path.stat().st_size
            asyncio.sleep(0.5)  # Небольшая задержка
            size2 = file_path.stat().st_size
            
            return size1 == size2 and size1 > 0
        except Exception:
            return False
            
    async def processing_loop(self):
        """Основной цикл обработки файлов."""
        while self.is_running:
            try:
                # Обрабатываем ожидающие файлы
                files_to_process = list(self.pending_files)
                self.pending_files.clear()
                
                for file_path in files_to_process:
                    if file_path not in self.processing_tasks:
                        task = asyncio.create_task(
                            self.process_audio_file(file_path)
                        )
                        self.processing_tasks[file_path] = task
                
                # Очищаем завершенные задачи
                completed_tasks = [
                    path for path, task in self.processing_tasks.items() 
                    if task.done()
                ]
                for path in completed_tasks:
                    del self.processing_tasks[path]
                
                await asyncio.sleep(5)  # Проверяем каждые 5 секунд
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле обработки: {e}")
                await asyncio.sleep(10)
                
    async def process_audio_file(self, file_path: str):
        """Обработка одного аудиофайла."""
        try:
            path_obj = Path(file_path)
            
            # Проверяем готовность файла
            if not self.is_file_ready(path_obj):
                await asyncio.sleep(2)
                if not self.is_file_ready(path_obj):
                    logger.warning(f"⏸️ Файл не готов: {path_obj.name}")
                    return
            
            # Добавляем в базу данных
            fragment = await self.add_file_to_database(path_obj)
            if not fragment:
                return
                
            # Запускаем транскрипцию
            await self.transcribe_fragment(fragment)
            
            self.processed_files.add(file_path)
            logger.info(f"✅ Файл обработан: {path_obj.name}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки файла {file_path}: {e}")
            
    async def add_file_to_database(self, file_path: Path) -> Fragment:
        """Добавление файла в базу данных."""
        try:
            # Парсим дату из пути файла
            date_str = self.extract_date_from_path(file_path)
            if not date_str:
                logger.warning(f"⚠️ Не удалось извлечь дату из пути: {file_path}")
                return None
                
            file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Парсим время начала из имени файла
            start_time = self.extract_start_time_from_filename(file_path.name, file_date)
            
            db = get_db_sync()
            try:
                # Находим или создаем день
                day = db.query(Day).filter(Day.date == file_date).first()
                if not day:
                    day = Day(date=file_date)
                    db.add(day)
                    db.commit()
                    db.refresh(day)
                
                # Проверяем, не существует ли уже этот фрагмент
                existing_fragment = db.query(Fragment).filter(
                    Fragment.file_path == str(file_path)
                ).first()
                
                if existing_fragment:
                    return existing_fragment
                
                # Создаем новый фрагмент
                file_stats = file_path.stat()
                fragment = Fragment(
                    day_id=day.id,
                    file_path=str(file_path),
                    original_filename=file_path.name,
                    file_size_bytes=file_stats.st_size,
                    start_time=start_time,
                    sample_rate=16000,  # Из конфигурации Pi
                    channels=1
                )
                
                # Обновляем статистику дня
                day.total_fragments += 1
                
                db.add(fragment)
                db.commit()
                db.refresh(fragment)
                
                logger.info(f"📝 Фрагмент добавлен в БД: {fragment.original_filename}")
                return fragment
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления в БД: {e}")
            return None
    
    async def transcribe_fragment(self, fragment: Fragment):
        """Транскрипция фрагмента через Whisper."""
        try:
            result = await self.whisper_processor.transcribe_file(fragment.file_path)
            
            if result:
                db = get_db_sync()
                try:
                    # Обновляем фрагмент результатами транскрипции
                    db_fragment = db.query(Fragment).filter(Fragment.id == fragment.id).first()
                    if db_fragment:
                        db_fragment.transcript_text = result.get("text", "")
                        db_fragment.whisper_segments = result.get("segments", [])
                        db_fragment.whisper_model_used = result.get("model", "unknown")
                        db_fragment.transcribed = True
                        db_fragment.transcription_completed_at = datetime.utcnow()
                        db_fragment.duration_seconds = result.get("duration", None)
                        
                        # Обновляем продолжительность дня
                        if db_fragment.duration_seconds:
                            day = db.query(Day).filter(Day.id == db_fragment.day_id).first()
                            if day:
                                day.total_duration_seconds += db_fragment.duration_seconds
                        
                        db.commit()
                        logger.info(f"🎯 Транскрипция завершена: {fragment.original_filename}")
                        
                finally:
                    db.close()
                    
        except Exception as e:
            logger.error(f"❌ Ошибка транскрипции {fragment.original_filename}: {e}")
            
            # Записываем ошибку в базу
            db = get_db_sync()
            try:
                db_fragment = db.query(Fragment).filter(Fragment.id == fragment.id).first()
                if db_fragment:
                    db_fragment.processing_error = str(e)
                    db_fragment.retry_count += 1
                    db.commit()
            finally:
                db.close()
    
    def extract_date_from_path(self, file_path: Path) -> str:
        """Извлечение даты из пути файла."""
        # Ожидаем структуру: /recordings/YYYY-MM-DD/filename.wav
        parts = file_path.parts
        for part in reversed(parts):
            if len(part) == 10 and part.count('-') == 2:
                try:
                    datetime.strptime(part, "%Y-%m-%d")
                    return part
                except ValueError:
                    continue
        return None
    
    def extract_start_time_from_filename(self, filename: str, date: datetime.date) -> datetime:
        """Извлечение времени начала из имени файла."""
        # Ожидаем формат: YYYY-MM-DD_HH-MM-SS.wav
        try:
            base_name = filename.replace('.wav', '')
            if '_' in base_name:
                time_part = base_name.split('_')[1]
                time_str = time_part.replace('-', ':')
                return datetime.combine(date, datetime.strptime(time_str, "%H:%M:%S").time())
        except Exception:
            pass
            
        # Fallback - используем время создания файла
        return datetime.combine(date, datetime.now().time())
    
    def get_stats(self) -> dict:
        """Получение статистики file watcher."""
        return {
            "is_running": self.is_running,
            "pending_files": len(self.pending_files),
            "processing_tasks": len(self.processing_tasks),
            "processed_files": len(self.processed_files),
            "recordings_path": str(self.recordings_path)
        } 