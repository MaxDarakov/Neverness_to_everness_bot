from flask import Flask
from threading import Thread
import os
import sqlite3

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

TOKEN = os.getenv("TOKEN")
DB_FILE = "tasks.db"

# ---------------- FLASK ----------------

app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# ---------------- DB ----------------

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            date TEXT,
            time TEXT,
            frequency TEXT,
            done INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_task(name, date, time, freq):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (name, date, time, frequency, done) VALUES (?, ?, ?, ?, 0)",
        (name, date, time, freq)
    )
    conn.commit()
    conn.close()

def get_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM tasks")
    rows = c.fetchall()
    conn.close()
    return rows

def toggle_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = NOT done WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# ---------------- FSM STATES ----------------

NAME, DATE, TIME, FREQ = range(4)

user_data_temp = {}

# ---------------- START MENU ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["➕ Створити задачу"],
        ["📋 Список задач"]
    ]

    await update.message.reply_text(
        "📌 Меню:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# ---------------- CREATE FLOW ----------------

async def create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Введи назву задачі:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_data_temp[update.effective_user.id] = {}
    user_data_temp[update.effective_user.id]["name"] = update.message.text

    await update.message.reply_text("Введи дату (YYYY-MM-DD):")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_data_temp[update.effective_user.id]["date"] = update.message.text

    await update.message.reply_text("Введи час (HH:MM):")
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_data_temp[update.effective_user.id]["time"] = update.message.text

    await update.message.reply_text("Частота: daily / weekly / monthly / once")
    return FREQ

async def get_freq(update: Update, context: ContextTypes.DEFAULT_TYPE):

    freq = update.message.text.lower()
    uid = update.effective_user.id

    if freq not in ["daily", "weekly", "monthly", "once"]:
        await update.message.reply_text("Невірна частота")
        return FREQ

    data = user_data_temp.get(uid)

    add_task(
        data["name"],
        data["date"],
        data["time"],
        freq
    )

    await update.message.reply_text("✅ Задачу створено!")

    return ConversationHandler.END

# ---------------- LIST ----------------

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    tasks = get_tasks()

    if not tasks:
        await update.message.reply_text("Порожньо")
        return

    text = "📋 Задачі:\n\n"
    keyboard = []

    for t in tasks:
        tid, name, date, time, freq, done = t

        status = "✅" if done else "❌"

        text += f"{tid}. {status} {name}\n{date} {time} ({freq})\n\n"

        keyboard.append([
            InlineKeyboardButton(
                f"{status} {name}",
                callback_data=str(tid)
            )
        ])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- TOGGLE ----------------

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    toggle_task(int(query.data))

    await list_tasks(update, context)

# ---------------- RUN ----------------

def run_bot():

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("➕ Створити задачу"), create_start)
        ],
        states={
            NAME: [MessageHandler(filters.TEXT, get_name)],
            DATE: [MessageHandler(filters.TEXT, get_date)],
            TIME: [MessageHandler(filters.TEXT, get_time)],
            FREQ: [MessageHandler(filters.TEXT, get_freq)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("📋 Список задач"), list_tasks))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button))

    print("Todo FSM bot started!")

    app.run_polling()

Thread(target=run_web).start()
run_bot()
