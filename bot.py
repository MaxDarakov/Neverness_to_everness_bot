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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["📌 Інфо", "🎮 Ігри"],
        ["😂 Мем", "❌ Закрити"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Привіт! Я працюю через Render 😎",
        reply_markup=reply_markup
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "📌 Інфо":
        await update.message.reply_text(
            "Я Telegram-бот."
        )

    elif text == "🎮 Ігри":
        await update.message.reply_text(
            "Minecraft, GTA V, Terraria"
        )

    elif text == "😂 Мем":
        await update.message.reply_text(
            "— Мамо, я програміст.\n— Тоді полагодь принтер."
        )

    elif text == "❌ Закрити":
        await update.message.reply_text(
            "Меню закрито."
        )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, buttons))

print("Бот запущений!")

app.run_polling()
