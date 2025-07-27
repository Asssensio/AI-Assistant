# 🏗️ Структура проекта AI-Assistant

## Основная структура

```
AI-Assistant/
├── 📁 raspberry-pi/           # Код для Raspberry Pi
│   ├── 📄 audio_recorder.py    # Основной скрипт записи
│   ├── 📄 file_sender.py       # Отправка файлов на ПК
│   ├── 📄 config.py           # Конфигурация Pi
│   ├── 📄 requirements.txt    # Зависимости для Pi
│   └── 📁 systemd/            # Службы systemd
│       └── 📄 audio-recorder.service
│
├── 📁 backend/                # Backend на ПК (FastAPI)
│   ├── 📁 app/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py         # FastAPI приложение
│   │   ├── 📁 api/            # API эндпоинты
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 auth.py     # JWT авторизация
│   │   │   ├── 📄 days.py     # API для дней
│   │   │   └── 📄 fragments.py # API для фрагментов
│   │   ├── 📁 core/           # Основная логика
│   │   │   ├── 📄 whisper_processor.py # Whisper интеграция
│   │   │   ├── 📄 summary_generator.py # Генерация summary
│   │   │   └── 📄 file_watcher.py     # Демон обработки файлов
│   │   ├── 📁 models/         # Модели данных
│   │   │   ├── 📄 database.py # Настройка БД
│   │   │   ├── 📄 day.py      # Модель дня
│   │   │   └── 📄 fragment.py # Модель фрагмента
│   │   └── 📁 utils/          # Утилиты
│   │       ├── 📄 auth.py     # JWT утилиты
│   │       └── 📄 time_utils.py # Работа с временем
│   ├── 📄 requirements.txt
│   └── 📄 Dockerfile          # Для будущего контейнеризации
│
├── 📁 telegram-bot/           # Telegram бот
│   ├── 📄 bot.py              # Основной файл бота
│   ├── 📄 handlers.py         # Обработчики команд
│   ├── 📄 chatgpt_client.py   # Интеграция с ChatGPT
│   ├── 📄 config.py           # Конфигурация бота
│   └── 📄 requirements.txt
│
├── 📁 frontend/               # Веб-интерфейс (Next.js или Vue)
│   ├── 📄 package.json
│   ├── 📁 src/
│   │   ├── 📁 components/     # React/Vue компоненты
│   │   ├── 📁 pages/          # Страницы
│   │   └── 📁 api/            # API клиент
│   └── 📄 Dockerfile
│
├── 📁 shared/                 # Общие компоненты
│   ├── 📄 __init__.py
│   ├── 📄 models.py           # Общие модели данных
│   ├── 📄 config.py           # Общая конфигурация
│   └── 📄 exceptions.py       # Общие исключения
│
├── 📁 tests/                  # Тесты
│   ├── 📁 unit/
│   ├── 📁 integration/
│   └── 📁 mocks/              # Мок-данные для разработки
│       ├── 📁 audio/          # Тестовые аудиофайлы
│       └── 📁 transcripts/    # Тестовые расшифровки
│
├── 📁 scripts/                # Скрипты развертывания и утилиты
│   ├── 📄 setup_pi.sh         # Настройка Raspberry Pi
│   ├── 📄 deploy_backend.sh   # Деплой backend
│   └── 📄 backup.sh           # Скрипт резервного копирования
│
├── 📁 docs/                   # Документация
│   ├── 📄 README.md
│   ├── 📄 API.md              # Документация API
│   ├── 📄 SETUP.md            # Инструкции по настройке
│   └── 📄 ARCHITECTURE.md     # Архитектура системы
│
├── 📁 config/                 # Конфигурационные файлы
│   ├── 📄 .env.example
│   ├── 📄 docker-compose.yml
│   └── 📁 nginx/              # Конфиги nginx (если понадобится)
│
├── 📄 pyproject.toml          # Poetry конфигурация
├── 📄 .gitignore
├── 📄 .pre-commit-config.yaml # Pre-commit хуки
└── 📄 README.md               # Основной README
```

## Альтернативные варианты структуры

### Вариант A: Монорепо с apps/
```
AI-Assistant/
├── apps/
│   ├── raspberry-pi/
│   ├── backend/
│   ├── telegram-bot/
│   └── frontend/
├── packages/
│   └── shared/
└── tools/
```

### Вариант B: Разделение по типу компонентов
```
AI-Assistant/
├── services/          # Все сервисы
│   ├── audio-recorder/
│   ├── whisper-processor/
│   ├── web-api/
│   └── telegram-bot/
├── clients/           # Клиентские приложения
│   └── web-ui/
└── shared/
```

## Рекомендация
Я склоняюсь к **основной структуре** - она интуитивна, масштабируема и четко разделяет ответственности. 