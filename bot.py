from flask import Flask
from threading import Thread
import os
import sqlite3
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("TOKEN")
DB_FILE = "tasks.db"

# ---------------- FLASK ----------------

app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Planner Bot is alive!"

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

def add_task_db(name, date, time, freq):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO tasks (name, date, time, frequency, done)
        VALUES (?, ?, ?, ?, 0)
    """, (name, date, time, freq))
    conn.commit()
    conn.close()

def get_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, date, time, frequency, done FROM tasks")
    rows = c.fetchall()
    conn.close()
    return rows

def toggle_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = NOT done WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# ---------------- ADD ----------------

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.replace("/add ", "")

    # name | date | time | freq
    if text.count("|") != 3:
        await update.message.reply_text(
            "Формат:\n/add Назва | YYYY-MM-DD | HH:MM | daily/weekly/monthly/once"
        )
        return

    name, date, time, freq = [x.strip() for x in text.split("|")]

    if freq not in ["daily", "weekly", "monthly", "once"]:
        await update.message.reply_text("freq: daily / weekly / monthly / once")
        return

    # проста перевірка дати/часу
    try:
        datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M")
    except:
        await update.message.reply_text("Невірна дата або час")
        return

    add_task_db(name, date, time, freq)

    await update.message.reply_text(f"✅ Додано: {name}")

# ---------------- LIST ----------------

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    tasks = get_tasks()

    if not tasks:
        await update.message.reply_text("📭 Порожньо")
        return

    text = "📋 Планер:\n\n"
    keyboard = []

    for t in tasks:
        tid, name, date, time, freq, done = t

        status = "✅" if done else "❌"

        text += f"{tid}. {status} {name}\n📅 {date} {time} ({freq})\n\n"

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

    task_id = int(query.data)

    toggle_task(task_id)

    await list_tasks(update, context)

# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📌 Планер бот\n\n"
        "/list\n"
        "/add Назва | дата | час | частота"
    )

# ---------------- RUN ----------------

def run_bot():

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CallbackQueryHandler(button))

    print("Planner bot started!")

    app.run_polling()

Thread(target=run_web).start()
run_bot()
