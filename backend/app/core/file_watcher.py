# путь: backend/app/core/file_watcher.py
"""
File Watcher для мониторинга новых аудиофайлов.
"""


class FileWatcher:
    """Мониторинг новых аудиофайлов."""
    
    def __init__(self):
        """Инициализация file watcher."""
        self.is_running = False
        
    async def start(self):
        """Запуск мониторинга."""
        self.is_running = True
        print("📁 File Watcher запущен")
        # TODO: Реализовать реальный мониторинг
        
    async def stop(self):
        """Остановка мониторинга."""
        self.is_running = False
        print("📁 File Watcher остановлен") 