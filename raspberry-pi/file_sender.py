# путь: raspberry-pi/file_sender.py
#!/usr/bin/env python3
"""
File Sender для передачи аудиофайлов с Raspberry Pi на ПК.

Отслеживает новые аудиофайлы и передаёт их на ПК через SSH/SCP.
"""

import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import hashlib

from libs.config import get_transfer_config
from libs.exceptions import FileTransferError


class FileSender:
    """Класс для отправки файлов с Pi на ПК."""
    
    def __init__(self) -> None:
        """Инициализация отправителя файлов."""
        self.config = get_transfer_config()
        self.sent_files: set = set()
        self.load_sent_files_cache()
        
    def load_sent_files_cache(self) -> None:
        """Загрузка кэша отправленных файлов."""
        cache_file = Path.home() / ".ai_assistant_sent_files"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.sent_files = set(line.strip() for line in f)
                print(f"Загружено {len(self.sent_files)} записей из кэша.")
            except Exception as e:
                print(f"Ошибка загрузки кэша: {e}")
                
    def save_sent_files_cache(self) -> None:
        """Сохранение кэша отправленных файлов."""
        cache_file = Path.home() / ".ai_assistant_sent_files"
        try:
            with open(cache_file, 'w') as f:
                for file_path in self.sent_files:
                    f.write(f"{file_path}\n")
        except Exception as e:
            print(f"Ошибка сохранения кэша: {e}")
            
    def get_file_hash(self, file_path: Path) -> str:
        """Получение хэша файла для проверки целостности."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Ошибка вычисления хэша для {file_path}: {e}")
            return ""
            
    def find_new_files(self) -> List[Path]:
        """Поиск новых аудиофайлов для отправки."""
        recordings_path = Path(self.config["source_path"])
        if not recordings_path.exists():
            return []
            
        new_files = []
        
        # Ищем WAV файлы во всех подпапках
        for wav_file in recordings_path.rglob("*.wav"):
            file_str = str(wav_file)
            if file_str not in self.sent_files:
                # Проверяем, что файл не изменяется (запись завершена)
                if self._is_file_ready(wav_file):
                    new_files.append(wav_file)
                    
        return sorted(new_files)
        
    def _is_file_ready(self, file_path: Path) -> bool:
        """Проверка готовности файла (завершена ли запись)."""
        try:
            # Проверяем размер файла с интервалом
            size1 = file_path.stat().st_size
            time.sleep(1)
            size2 = file_path.stat().st_size
            
            # Если размер не изменился и файл не пустой - готов
            return size1 == size2 and size1 > 0
        except Exception:
            return False
            
    def send_file(self, local_path: Path) -> bool:
        """Отправка одного файла на ПК."""
        try:
            # Формируем удалённый путь с сохранением структуры
            relative_path = local_path.relative_to(self.config["source_path"])
            remote_path = f"{self.config['remote_path']}/{relative_path}"
            
            # Создаём удалённую директорию
            remote_dir = str(Path(remote_path).parent)
            mkdir_cmd = [
                "ssh",
                f"{self.config['remote_user']}@{self.config['remote_host']}",
                f"mkdir -p {remote_dir}"
            ]
            
            result = subprocess.run(mkdir_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Ошибка создания удалённой директории: {result.stderr}")
                return False
                
            # Отправляем файл
            scp_cmd = [
                "scp",
                str(local_path),
                f"{self.config['remote_user']}@{self.config['remote_host']}:{remote_path}"
            ]
            
            print(f"Отправка: {local_path} -> {remote_path}")
            result = subprocess.run(scp_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Проверяем целостность файла
                if self._verify_remote_file(local_path, remote_path):
                    self.sent_files.add(str(local_path))
                    self.save_sent_files_cache()
                    print(f"✅ Файл отправлен: {local_path.name}")
                    return True
                else:
                    print(f"❌ Ошибка целостности файла: {local_path.name}")
                    return False
            else:
                print(f"❌ Ошибка отправки: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Исключение при отправке {local_path}: {e}")
            return False
            
    def _verify_remote_file(self, local_path: Path, remote_path: str) -> bool:
        """Проверка целостности отправленного файла."""
        try:
            # Получаем размер локального файла
            local_size = local_path.stat().st_size
            
            # Получаем размер удалённого файла
            size_cmd = [
                "ssh",
                f"{self.config['remote_user']}@{self.config['remote_host']}",
                f"stat -f%z {remote_path} 2>/dev/null || stat -c%s {remote_path}"
            ]
            
            result = subprocess.run(size_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                remote_size = int(result.stdout.strip())
                return local_size == remote_size
            else:
                return False
                
        except Exception as e:
            print(f"Ошибка проверки целостности: {e}")
            return False
            
    def cleanup_old_files(self, days_to_keep: int = 7) -> None:
        """Удаление старых локальных файлов после успешной отправки."""
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        recordings_path = Path(self.config["source_path"])
        
        removed_count = 0
        for wav_file in recordings_path.rglob("*.wav"):
            if str(wav_file) in self.sent_files:
                if wav_file.stat().st_mtime < cutoff_date:
                    try:
                        wav_file.unlink()
                        self.sent_files.discard(str(wav_file))
                        removed_count += 1
                    except Exception as e:
                        print(f"Ошибка удаления {wav_file}: {e}")
                        
        if removed_count > 0:
            print(f"🗑️ Удалено {removed_count} старых файлов")
            self.save_sent_files_cache()
            
    def start_monitoring(self, check_interval: int = 60) -> None:
        """Запуск мониторинга новых файлов."""
        print("📡 Запуск мониторинга файлов...")
        print(f"Источник: {self.config['source_path']}")
        print(f"Назначение: {self.config['remote_user']}@{self.config['remote_host']}:{self.config['remote_path']}")
        print(f"Интервал проверки: {check_interval} секунд")
        
        try:
            while True:
                # Ищем новые файлы
                new_files = self.find_new_files()
                
                if new_files:
                    print(f"📁 Найдено {len(new_files)} новых файлов")
                    
                    for file_path in new_files:
                        self.send_file(file_path)
                        time.sleep(1)  # Небольшая пауза между отправками
                        
                # Очистка старых файлов (раз в час)
                if int(time.time()) % 3600 == 0:
                    self.cleanup_old_files()
                    
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Мониторинг остановлен пользователем")
        except Exception as e:
            print(f"❌ Ошибка мониторинга: {e}")


def main() -> None:
    """Главная функция."""
    print("📡 AI Assistant File Sender")
    print("===========================")
    
    sender = FileSender()
    sender.start_monitoring()


if __name__ == "__main__":
    main() 