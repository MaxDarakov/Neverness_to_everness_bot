import os
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Перевірка версії бібліотеки
print("PTB version:", telegram.__version__)

# Отримуємо токен із Render Environment Variables
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ Помилка: Environment variable TOKEN не знайдено!")
    raise RuntimeError("Environment variable TOKEN is not set!")
else:
    print("✅ TOKEN знайдено, довжина:", len(TOKEN))

# Хендлер для команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привіт 👋!\n\n"
        "Я твій чекліст‑бот.\n"
        "Мої команди:\n"
        "• /start – показати це повідомлення\n"
        "• /checklist – відкрити список завдань\n\n"
        "✅ Натисни /checklist, щоб побачити свої завдання."
    )
    await update.message.reply_text(text)

def main():
    try:
        app = Application.builder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        print("🚀 Application створено, запускаю polling...")
        app.run_polling()
    except Exception as e:
        print("❌ Помилка при запуску бота:", e)

if __name__ == "__main__":
    main()
