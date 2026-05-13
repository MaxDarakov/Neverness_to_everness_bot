from flask import Flask
from threading import Thread
import os
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
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

# ---------------- DATABASE ----------------

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

def get_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, date, time, frequency, done FROM tasks")
    rows = c.fetchall()
    conn.close()
    return rows

def add_task_db(name, date, time, freq):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (name, date, time, frequency, done) VALUES (?, ?, ?, ?, 0)",
        (name, date, time, freq)
    )
    conn.commit()
    conn.close()

def toggle_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = NOT done WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def edit_task_name(task_id, new_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET name = ? WHERE id = ?", (new_name, task_id))
    conn.commit()
    conn.close()

# ---------------- UI RENDER ----------------

def render_keyboard(tasks):

    keyboard = []

    for t in tasks:
        tid, name, date, time, freq, done = t

        status = "✅" if done else "❌"

        keyboard.append([
            InlineKeyboardButton(
                f"{status} {name}",
                callback_data=f"toggle:{tid}"
            ),
            InlineKeyboardButton(
                "✏",
                callback_data=f"edit:{tid}"
            ),
            InlineKeyboardButton(
                "🗑",
                callback_data=f"delete:{tid}"
            ),
        ])

    return InlineKeyboardMarkup(keyboard)

def render_text(tasks):

    text = "📋 Чеклист:\n\n"

    for t in tasks:
        tid, name, date, time, freq, done = t
        status = "✅" if done else "❌"
        text += f"{tid}. {status} {name} ({freq})\n"

    return text

# ---------------- STATES (EDIT) ----------------

EDIT_MODE = {}

# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📌 Todo Bot\n\n"
        "/list - список\n"
        "/add Назва | YYYY-MM-DD | HH:MM | freq"
    )

# ---------------- ADD ----------------

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.replace("/add ", "")

    if text.count("|") != 3:
        await update.message.reply_text(
            "Формат:\n/add Назва | YYYY-MM-DD | HH:MM | daily/weekly/monthly/once"
        )
        return

    name, date, time, freq = [x.strip() for x in text.split("|")]

    if freq not in ["daily", "weekly", "monthly", "once"]:
        await update.message.reply_text("freq: daily / weekly / monthly / once")
