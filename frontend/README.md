# путь: frontend/README.md
# AI Assistant Frontend

Веб-интерфейс для системы речевой записи и анализа AI Assistant.

## 🚀 Быстрый старт

### Предварительные требования

- Node.js 18+ 
- npm или yarn
- Запущенный backend сервер (порт 8000)

### Установка и запуск

1. **Установите зависимости:**
```bash
npm install
```

2. **Создайте файл .env.local:**
```bash
cp .env.example .env.local
```

3. **Настройте переменные окружения:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. **Запустите в режиме разработки:**
```bash
npm run dev
```

5. **Откройте браузер:**
```
http://localhost:3000
```

## 🔐 Аутентификация

Для входа используйте:
- **Логин:** `admin`
- **Пароль:** `admin123`

## 🎵 Основные функции

### Аудиоплеер
- Визуализация waveform с помощью WaveSurfer.js
- Объединение аудиофрагментов в единый трек
- Синхронизация с текстом транскрипции
- Управление воспроизведением (play/pause, громкость, seek)

### Синхронизированный текст
- Подсветка текущего сегмента во время воспроизведения
- Клик по тексту для перехода к моменту в аудио
- Автопрокрутка к активному сегменту
- Парсинг timestamps из Whisper

### Редактор ретроспективы
- Блочное редактирование текста
- Объединение и удаление блоков
- Сохранение изменений в базу данных
- Предварительный просмотр

### Генерация summary
- Создание краткого summary через OpenAI
- Интеграция с ChatGPT API
- Автоматическое обновление интерфейса

## 🛠 Технологии

- **Next.js 15** - React фреймворк
- **TypeScript** - Типизация
- **Tailwind CSS** - Стилизация
- **WaveSurfer.js** - Аудио визуализация
- **Axios** - HTTP клиент
- **Lucide React** - Иконки

## 📁 Структура проекта

```
src/
├── app/                    # App Router (Next.js 13+)
│   ├── day/[date]/        # Страница дня
│   ├── days/              # Список дней
│   ├── login/             # Страница входа
│   └── layout.tsx         # Корневой layout
├── components/            # React компоненты
│   ├── AudioPlayer.tsx    # Аудиоплеер
│   ├── SynchronizedText.tsx # Синхронизированный текст
│   └── RetrospectiveEditor.tsx # Редактор
├── contexts/              # React контексты
│   └── AuthContext.tsx    # Аутентификация
├── lib/                   # Утилиты
│   └── api.ts            # API клиент
└── middleware.ts          # Next.js middleware
```

## 🔧 Разработка

### Команды

```bash
# Запуск в режиме разработки
npm run dev

# Сборка для продакшена
npm run build

# Запуск продакшен сборки
npm start

# Линтинг
npm run lint

# Типизация
npm run type-check
```

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `NEXT_PUBLIC_API_URL` | URL backend API | `http://localhost:8000` |

## 🎨 UI/UX

### Дизайн система
- **Цвета:** Синяя палитра (#4F46E5, #7C3AED)
- **Типографика:** Geist Sans (системный шрифт)
- **Компоненты:** Tailwind CSS + кастомные стили
- **Анимации:** CSS transitions + Framer Motion

### Адаптивность
- Mobile-first подход
- Responsive breakpoints
- Touch-friendly интерфейс

## 🔒 Безопасность

- JWT токены в localStorage
- Защищенные роуты через middleware
- Автоматический редирект на логин
- Валидация форм

## 🚀 Деплой

### Vercel (рекомендуется)
```bash
npm run build
vercel --prod
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 📝 Лицензия

MIT License
