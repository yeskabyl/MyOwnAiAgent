# 🤖 Telegram Code Agent Bot

Telegram-бот на Python, который пишет код за тебя с помощью Gemini AI.

## Возможности

- ✅ Пишет код на любом языке (Python, JS, SQL, Go, Bash и др.)
- ✅ Помнит контекст диалога — можно уточнять задачи
- ✅ Исправляет и объясняет чужой код
- ✅ Пишет тесты, документацию, оптимизирует код
- ✅ Отправляет длинные ответы частями без обрезки

## Установка

### 1. Получи токены

**Telegram Bot Token:**
1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. Напиши `/newbot` и следуй инструкциям
3. Скопируй токен вида `123456789:AAF...`

**Gemini API Key:**
1. Зайди на [aistudio.google.com](https://aistudio.google.com/apikey)
2. Нажми **Get API key** → **Create API key**

### 2. Установи зависимости

```bash
pip install -r requirements.txt
```

### 3. Задай переменные окружения

**Linux / macOS:**
```bash
export TELEGRAM_BOT_TOKEN="твой_токен_бота"
export GEMINI_API_KEY="твой_gemini_ключ"
```

**Windows (PowerShell):**
```powershell
$env:TELEGRAM_BOT_TOKEN="твой_токен_бота"
$env:GEMINI_API_KEY="твой_gemini_ключ"
```

**Или создай файл `.env`** и используй `python-dotenv`:
```env
TELEGRAM_BOT_TOKEN=твой_токен_бота
GEMINI_API_KEY=твой_gemini_ключ
```

### 4. Запусти бота

```bash
python bot.py
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начало работы, примеры запросов |
| `/new` | Очистить историю диалога |
| `/help` | Справка |

## Примеры запросов

- *Напиши парсер сайта на Python с использованием BeautifulSoup*
- *Сделай REST API на FastAPI с авторизацией через JWT*
- *Напиши SQL запрос для поиска дубликатов в таблице*
- *Исправь ошибку в этом коде: [вставь код]*
- *Напиши Docker Compose для Flask + PostgreSQL + Redis*

## Деплой на сервер (опционально)

```bash
# Создай systemd сервис
sudo nano /etc/systemd/system/code-bot.service
```

```ini
[Unit]
Description=Telegram Code Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/code-bot
Environment=TELEGRAM_BOT_TOKEN=твой_токен
Environment=GEMINI_API_KEY=твой_ключ
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable code-bot
sudo systemctl start code-bot
```
