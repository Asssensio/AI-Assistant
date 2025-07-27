#!/usr/bin/env python3
"""
Audio Recorder for Raspberry Pi Zero 2W with ReSpeaker 2-Mic HAT.

Записывает аудио в формате WAV, mono, 16 kHz каждые 10 минут.
Сохраняет файлы в структуре /recordings/YYYY-MM-DD/YYYY-MM-DD_HH-MM-SS.wav
"""

import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    import pyaudio
    import wave
except ImportError:
    print("Warning: pyaudio not available. Running in mock mode.")
    pyaudio = None
    wave = None

from libs.config import get_audio_config
from libs.exceptions import AudioRecordingError


class AudioRecorder:
    """Класс для записи аудио на Raspberry Pi."""
    
    def __init__(self) -> None:
        """Инициализация рекордера."""
        self.config = get_audio_config()
        self.is_recording = False
        self.stream: Optional[object] = None
        self.audio: Optional[object] = None
        
        # Настройка обработчика сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, sig: int, frame) -> None:
        """Обработчик сигналов для корректного завершения."""
        print(f"\nПолучен сигнал {sig}. Завершение записи...")
        self.stop_recording()
        sys.exit(0)
        
    def _setup_audio(self) -> bool:
        """Настройка аудио устройства."""
        if pyaudio is None:
            print("PyAudio не установлен. Работаю в мок-режиме.")
            return False
            
        try:
            self.audio = pyaudio.PyAudio()
            
            # Поиск ReSpeaker устройства
            device_index = self._find_respeaker_device()
            if device_index is None:
                print("ReSpeaker устройство не найдено. Использую устройство по умолчанию.")
                device_index = None
                
            self.device_index = device_index
            return True
            
        except Exception as e:
            print(f"Ошибка настройки аудио: {e}")
            return False
            
    def _find_respeaker_device(self) -> Optional[int]:
        """Поиск ReSpeaker 2-Mic HAT устройства."""
        if self.audio is None:
            return None
            
        device_count = self.audio.get_device_count()
        for i in range(device_count):
            info = self.audio.get_device_info_by_index(i)
            if "respeaker" in info["name"].lower() or "seeed" in info["name"].lower():
                print(f"Найдено ReSpeaker устройство: {info['name']}")
                return i
        return None
        
    def _get_output_path(self, timestamp: datetime) -> Path:
        """Получение пути для сохранения файла."""
        date_str = timestamp.strftime("%Y-%m-%d")
        filename = timestamp.strftime("%Y-%m-%d_%H-%M-%S.wav")
        
        output_dir = Path(self.config["base_path"]) / date_str
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir / filename
        
    def record_chunk(self, duration_minutes: int = 10) -> Path:
        """Запись одного фрагмента аудио."""
        timestamp = datetime.now()
        output_path = self._get_output_path(timestamp)
        
        print(f"Начало записи: {output_path}")
        
        if pyaudio is None or wave is None:
            # Мок-режим: создаём пустой файл
            output_path.touch()
            print(f"Мок-запись завершена: {output_path}")
            return output_path
            
        try:
            # Настройка параметров записи
            chunk = 1024
            sample_format = pyaudio.paInt16
            channels = self.config["channels"]
            sample_rate = self.config["sample_rate"]
            record_seconds = duration_minutes * 60
            
            # Открытие потока
            stream = self.audio.open(
                format=sample_format,
                channels=channels,
                rate=sample_rate,
                frames_per_buffer=chunk,
                input=True,
                input_device_index=getattr(self, 'device_index', None)
            )
            
            frames = []
            
            # Запись
            for i in range(0, int(sample_rate / chunk * record_seconds)):
                if not self.is_recording:
                    break
                data = stream.read(chunk)
                frames.append(data)
                
                # Прогресс каждые 30 секунд
                if i % (sample_rate // chunk * 30) == 0:
                    elapsed = i * chunk / sample_rate
                    print(f"Записано: {elapsed:.0f}/{record_seconds} секунд")
            
            # Закрытие потока
            stream.stop_stream()
            stream.close()
            
            # Сохранение файла
            with wave.open(str(output_path), 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(self.audio.get_sample_size(sample_format))
                wf.setframerate(sample_rate)
                wf.writeframes(b''.join(frames))
                
            print(f"Запись завершена: {output_path}")
            return output_path
            
        except Exception as e:
            raise AudioRecordingError(f"Ошибка записи аудио: {e}")
            
    def start_continuous_recording(self) -> None:
        """Запуск непрерывной записи с 10-минутными фрагментами."""
        print("Запуск непрерывной записи аудио...")
        
        if not self._setup_audio():
            print("Работаю в мок-режиме без реального аудио.")
            
        self.is_recording = True
        
        try:
            while self.is_recording:
                # Записываем фрагмент
                output_path = self.record_chunk(10)
                
                # Небольшая пауза между фрагментами
                if self.is_recording:
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\nПрерывание пользователем.")
        except Exception as e:
            print(f"Ошибка в процессе записи: {e}")
        finally:
            self.stop_recording()
            
    def stop_recording(self) -> None:
        """Остановка записи."""
        self.is_recording = False
        if self.audio:
            self.audio.terminate()
        print("Запись остановлена.")


def main() -> None:
    """Главная функция."""
    print("🎙️ AI Assistant Audio Recorder")
    print("================================")
    
    recorder = AudioRecorder()
    recorder.start_continuous_recording()


if __name__ == "__main__":
    main() 