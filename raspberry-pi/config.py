# путь: raspberry-pi/config.py
"""
Конфигурация специфичная для Raspberry Pi компонентов.
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Загружаем конфигурацию Pi
env_file = Path.home() / "ai-assistant" / ".env.pi"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()  # Fallback к обычному .env


def get_pi_audio_config() -> Dict[str, Any]:
    """Конфигурация аудио для Raspberry Pi."""
    return {
        "sample_rate": int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
        "channels": int(os.getenv("AUDIO_CHANNELS", "1")),
        "chunk_size": int(os.getenv("AUDIO_CHUNK_SIZE", "1024")),
        "format": os.getenv("AUDIO_FORMAT", "WAV"),
        "chunk_minutes": int(os.getenv("RECORDING_CHUNK_MINUTES", "10")),
        "base_path": Path(os.getenv("RECORDINGS_BASE_PATH", "/home/pi/recordings")),
        "device_name_patterns": ["respeaker", "seeed", "usb"],
    }


def get_pi_transfer_config() -> Dict[str, Any]:
    """Конфигурация передачи файлов с Pi на ПК."""
    return {
        "pc_host": os.getenv("PC_HOST", "192.168.1.100"),
        "pc_user": os.getenv("PC_USER", "user"),
        "pc_path": os.getenv("PC_RECORDINGS_PATH", "/recordings"),
        "ssh_key_path": Path(os.getenv("PI_SSH_KEY_PATH", "/home/pi/.ssh/id_rsa")),
        "verification_enabled": True,
        "cleanup_days": int(os.getenv("CLEANUP_DAYS", "7")),
        "check_interval": int(os.getenv("CHECK_INTERVAL", "60")),
    }


def get_pi_system_config() -> Dict[str, Any]:
    """Системная конфигурация Pi."""
    return {
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "max_retries": int(os.getenv("MAX_RETRIES", "3")),
        "retry_delay": int(os.getenv("RETRY_DELAY", "30")),
        "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "300")),
    } 