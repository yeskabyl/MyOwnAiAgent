import asyncio
import logging
import os
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode, ChatAction

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Инициализация Gemini клиента
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
gemini_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=None,  # будет задан ниже после объявления SYSTEM_PROMPT
)

# Хранилище истории диалогов (в памяти)
# Для продакшена используй Redis или БД
user_sessions: dict[int, list[dict]] = {}

SYSTEM_PROMPT = """Ты — опытный AI-агент разработчик. Твоя задача — писать качественный, рабочий код по запросу пользователя.

Правила:
1. Всегда пиши чистый, читаемый и документированный код
2. Используй актуальные практики и паттерны для каждого языка
3. Объясняй что делает код, если это не очевидно
4. Если задача большая — разбивай на части и спрашивай уточнения
5. Если видишь потенциальные ошибки или улучшения — указывай на них
6. Форматируй код в блоки с указанием языка
7. Если пользователь просит исправить код — анализируй ошибку и объясняй причину
8. Отвечай на русском языке, если пользователь пишет на русском

Ты умеешь работать с любыми языками программирования: Python, JavaScript, TypeScript, Go, Rust, Java, C++, SQL и другими."""

# Пересоздаём модель с system_instruction
gemini_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT,
)


def get_or_create_session(user_id: int) -> list[dict]:
    """Получить или создать сессию для пользователя."""
    if user_id not in user_sessions:
        user_sessions[user_id] = []
    return user_sessions[user_id]


def format_code_message(text: str) -> str:
    """Подготовить текст для Telegram (ограничение 4096 символов)."""
    if len(text) <= 4096:
        return text
    return text[:4090] + "\n..."


async def send_long_message(update: Update, text: str):
    """Отправить длинное сообщение, разбив на части если нужно."""
    max_len = 4096
    if len(text) <= max_len:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    # Разбиваем по блокам кода чтобы не ломать форматирование
    parts = []
    current = ""
    in_code_block = False

    for line in text.split("\n"):
        if line.startswith("```"):
            in_code_block = not in_code_block

        if len(current) + len(line) + 1 > max_len and not in_code_block:
            parts.append(current)
            current = line + "\n"
        else:
            current += line + "\n"

    if current:
        parts.append(current)

    for part in parts:
        try:
            await update.message.reply_text(part.strip(), parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # Если Markdown не парсится — отправляем без форматирования
            await update.message.reply_text(part.strip())
        await asyncio.sleep(0.3)


async def ask_gemini(user_id: int, user_message: str) -> str:
    """Отправить запрос к Gemini с историей диалога."""
    history = get_or_create_session(user_id)

    # Ограничиваем историю последними 20 сообщениями (10 пар)
    if len(history) > 20:
        history = history[-20:]
        user_sessions[user_id] = history

    # Формат истории для Gemini: role "user" / "model"
    gemini_history = [
        {"role": msg["role"] if msg["role"] == "user" else "model", "parts": [msg["content"]]}
        for msg in history
    ]

    chat = gemini_model.start_chat(history=gemini_history)
    response = await asyncio.to_thread(chat.send_message, user_message)
    assistant_message = response.text

    history.append({"role": "user", "content": user_message})
    history.append({"role": "model", "content": assistant_message})

    return assistant_message


# ─── Handlers ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start."""
    keyboard = [
        [
            InlineKeyboardButton("🐍 Python", callback_data="example_python"),
            InlineKeyboardButton("🌐 JavaScript", callback_data="example_js"),
        ],
        [
            InlineKeyboardButton("🗄️ SQL запрос", callback_data="example_sql"),
            InlineKeyboardButton("🔧 Bash скрипт", callback_data="example_bash"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Привет! Я AI-агент разработчик на базе Gemini.\n\n"
        "💬 Просто напиши что нужно написать, например:\n"
        "• *Напиши парсер сайта на Python*\n"
        "• *Сделай REST API на FastAPI*\n"
        "• *Напиши SQL запрос для...*\n"
        "• *Исправь эту ошибку: [вставь код]*\n\n"
        "🔧 Команды:\n"
        "/start — начало\n"
        "/new — очистить историю диалога\n"
        "/help — помощь\n\n"
        "Или выбери пример:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help."""
    await update.message.reply_text(
        "🤖 *Как использовать бота:*\n\n"
        "1. Напиши задачу на русском или английском\n"
        "2. Можешь вставить код для исправления\n"
        "3. Бот помнит контекст диалога — можешь уточнять\n\n"
        "*Примеры запросов:*\n"
        "• Напиши телеграм бота на aiogram\n"
        "• Сделай класс для работы с Redis\n"
        "• Объясни что делает этот код: `[код]`\n"
        "• Оптимизируй эту функцию\n"
        "• Напиши тесты для этого кода\n\n"
        "/new — начать новый диалог (очистить историю)",
        parse_mode=ParseMode.MARKDOWN,
    )


async def new_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /new — очистить историю."""
    user_id = update.effective_user.id
    user_sessions[user_id] = []
    await update.message.reply_text(
        "🗑️ История очищена. Начинаем новый диалог!"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений."""
    user_id = update.effective_user.id
    user_text = update.message.text

    # Показываем индикатор набора
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    try:
        response = await ask_gemini(user_id, user_text)
        await send_long_message(update, response)
    except Exception as e:
        logger.error(f"Ошибка при запросе к Gemini: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обращении к AI. Попробуй ещё раз.\n"
            f"Детали: `{str(e)[:200]}`",
            parse_mode=ParseMode.MARKDOWN,
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки."""
    query = update.callback_query
    await query.answer()

    examples = {
        "example_python": "Напиши функцию на Python которая парсит JSON файл и сохраняет данные в SQLite базу данных",
        "example_js": "Напиши React компонент — форму авторизации с валидацией email и пароля",
        "example_sql": "Напиши SQL запрос который находит топ-10 клиентов по сумме заказов за последний месяц",
        "example_bash": "Напиши bash скрипт для автоматического бэкапа папки с архивацией и отправкой на удалённый сервер по SCP",
    }

    if query.data in examples:
        user_id = query.from_user.id
        example_text = examples[query.data]

        await query.message.reply_text(f"📝 Запрос: _{example_text}_", parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_chat_action(
            chat_id=query.message.chat_id,
            action=ChatAction.TYPING,
        )

        try:
            response = await ask_gemini(user_id, example_text)
            # Отправляем через новый update-подобный объект
            class FakeUpdate:
                message = query.message

            await send_long_message(FakeUpdate(), response)
        except Exception as e:
            await query.message.reply_text(f"❌ Ошибка: {str(e)[:200]}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    token = os.environ.get("8524342556:AAHRB41juR7n_-6F6DRxVnOgG9S2DmlVrH8")
    if not token:
        raise ValueError("Переменная окружения TELEGRAM_BOT_TOKEN не задана!")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_session))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()