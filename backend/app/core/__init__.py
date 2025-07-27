"""Основная бизнес-логика backend."""

from .file_watcher import FileWatcher
from .whisper_processor import WhisperProcessor
 
__all__ = ["FileWatcher", "WhisperProcessor"] 