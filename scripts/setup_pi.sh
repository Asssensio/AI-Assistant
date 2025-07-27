#!/bin/bash

# AI Assistant - Скрипт настройки Raspberry Pi Zero 2W
# Устанавливает все необходимые зависимости и настраивает систему

set -e  # Выход при любой ошибке

echo "🍓 AI Assistant - Настройка Raspberry Pi"
echo "========================================"

# Проверка запуска от root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Этот скрипт не должен запускаться от root"
   exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка базовых пакетов
echo "📦 Установка базовых пакетов..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    nano \
    htop \
    rsync \
    openssh-client \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils

# Установка Poetry
echo "📦 Установка Poetry..."
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3 -
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
fi

# Настройка аудио для ReSpeaker HAT
echo "🎤 Настройка ReSpeaker 2-Mic HAT..."

# Включение SPI и I2C
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0

# Создание конфигурации ALSA
cat << 'EOF' | sudo tee /etc/asound.conf
pcm.!default {
    type asym
    playback.pcm {
        type plug
        slave.pcm "hw:0,0"
    }
    capture.pcm {
        type plug
        slave.pcm "hw:1,0"
    }
}

ctl.!default {
    type hw
    card 1
}
EOF

# Установка Python зависимостей для Pi
echo "🐍 Установка Python зависимостей..."
sudo apt install -y \
    python3-dev \
    python3-pyaudio \
    libasound2-dev \
    portaudio19-dev \
    python3-numpy \
    python3-scipy

# Создание директорий проекта
echo "📁 Создание директорий..."
mkdir -p ~/ai-assistant
mkdir -p ~/recordings
mkdir -p ~/.ssh

# Настройка SSH ключей
echo "🔑 Настройка SSH..."
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "Генерация SSH ключа..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    echo "📋 Публичный ключ для добавления на ПК:"
    echo "======================================="
    cat ~/.ssh/id_rsa.pub
    echo "======================================="
    echo "Скопируйте этот ключ и добавьте его на ваш ПК"
    read -p "Нажмите Enter когда будете готовы продолжить..."
fi

# Создание конфигурации для рекордера
cat << 'EOF' > ~/ai-assistant/.env.pi
# Конфигурация для Raspberry Pi
RECORDINGS_BASE_PATH=/home/pi/recordings
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1
RECORDING_CHUNK_MINUTES=10

# Настройки передачи файлов (обновите под ваши настройки)
PC_HOST=192.168.1.100
PC_USER=user
PC_RECORDINGS_PATH=/recordings
PI_SSH_KEY_PATH=/home/pi/.ssh/id_rsa
EOF

# Создание systemd сервиса для аудио рекордера
cat << 'EOF' | sudo tee /etc/systemd/system/ai-assistant-recorder.service
[Unit]
Description=AI Assistant Audio Recorder
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=audio
WorkingDirectory=/home/pi/ai-assistant
Environment=PATH=/home/pi/.local/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/home/pi/ai-assistant/.env.pi
ExecStart=/home/pi/.local/bin/poetry run python raspberry-pi/audio_recorder.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Создание systemd сервиса для file sender
cat << 'EOF' | sudo tee /etc/systemd/system/ai-assistant-sender.service
[Unit]
Description=AI Assistant File Sender
After=network.target ai-assistant-recorder.service
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/ai-assistant
Environment=PATH=/home/pi/.local/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/home/pi/ai-assistant/.env.pi
ExecStart=/home/pi/.local/bin/poetry run python raspberry-pi/file_sender.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Настройка пользователя audio группы
echo "👤 Настройка пользователя..."
sudo usermod -a -G audio pi

# Перезагрузка systemd
sudo systemctl daemon-reload

echo ""
echo "✅ Настройка Raspberry Pi завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Перезагрузите Raspberry Pi: sudo reboot"
echo "2. Скопируйте SSH ключ на ваш ПК"
echo "3. Обновите настройки в .env.pi файле"
echo "4. Клонируйте проект: git clone <repo-url> ~/ai-assistant"
echo "5. Установите зависимости: cd ~/ai-assistant && poetry install --with pi"
echo "6. Запустите сервисы:"
echo "   sudo systemctl enable ai-assistant-recorder"
echo "   sudo systemctl enable ai-assistant-sender"
echo "   sudo systemctl start ai-assistant-recorder"
echo "   sudo systemctl start ai-assistant-sender"
echo ""
echo "🔍 Проверка статуса:"
echo "   sudo systemctl status ai-assistant-recorder"
echo "   sudo systemctl status ai-assistant-sender"
echo "   journalctl -u ai-assistant-recorder -f"
echo ""

# Проверка аудио устройств
echo "🎤 Доступные аудио устройства:"
arecord -l || true

echo ""
echo "🎉 Настройка завершена успешно!" 