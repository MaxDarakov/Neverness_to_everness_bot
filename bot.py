from flask import Flask
from threading import Thread
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import os

TOKEN = os.getenv("TOKEN")

# Flask сервер
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# Telegram bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["📌 Інфо", "🎮 Ігри"],
        ["😂 Мем"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Render бот працює 😎",
        reply_markup=reply_markup
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "📌 Інфо":
        await update.message.reply_text("Я Telegram-бот.")

    elif text == "🎮 Ігри":
        await update.message.reply_text("Minecraft, Terraria")

    elif text == "😂 Мем":
        await update.message.reply_text("404 humor not found")

def run_bot():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, buttons))

    print("Бот запущений!")

    app.run_polling()

# Запуск Flask окремим потоком
Thread(target=run_web).start()

# Запуск бота
run_bot()
