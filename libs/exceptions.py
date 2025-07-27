"""
Кастомные исключения для AI Assistant.

Определяет специфичные для домена исключения для лучшей обработки ошибок.
"""


class AIAssistantError(Exception):
    """Базовое исключение для AI Assistant."""
    pass


class ConfigurationError(AIAssistantError):
    """Ошибка конфигурации."""
    pass


class AudioRecordingError(AIAssistantError):
    """Ошибка записи аудио."""
    pass


class FileTransferError(AIAssistantError):
    """Ошибка передачи файлов."""
    pass


class WhisperProcessingError(AIAssistantError):
    """Ошибка обработки Whisper."""
    pass


class DatabaseError(AIAssistantError):
    """Ошибка базы данных."""
    pass


class AuthenticationError(AIAssistantError):
    """Ошибка аутентификации."""
    pass


class TelegramBotError(AIAssistantError):
    """Ошибка Telegram бота."""
    pass


class SummaryGenerationError(AIAssistantError):
    """Ошибка генерации summary."""
    pass 