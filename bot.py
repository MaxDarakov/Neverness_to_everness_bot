from flask import Flask
from threading import Thread
import os
import sqlite3

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------------- CONFIG ----------------

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
            type TEXT,
            done INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_task_db(name, task_type):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (name, type, done) VALUES (?, ?, 0)", (name, task_type))
    conn.commit()
    conn.close()

def get_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, type, done FROM tasks")
    rows = c.fetchall()
    conn.close()
    return rows

def toggle_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = NOT done WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def delete_task_db(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# ---------------- UI ----------------

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):

    tasks = get_tasks()

    if not tasks:
        await update.message.reply_text("📭 Список порожній")
        return

    text = "📋 Чеклист:\n\n"
    keyboard = []

    for t in tasks:
        tid, name, task_type, done = t

        status = "✅" if done else "❌"

        text += f"{tid}. {status} {name} ({task_type})\n"

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

# ---------------- ADD ----------------

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.replace("/add ", "")

    if "|" not in text:
        await update.message.reply_text("Формат:\n/add Назва | daily")
        return

    name, task_type = text.split("|")

    name = name.strip()
    task_type = task_type.strip().lower()

    if task_type not in ["daily", "weekly", "monthly"]:
        await update.message.reply_text("Тип: daily / weekly / monthly")
        return

    add_task_db(name, task_type)

    await update.message.reply_text(f"✅ Додано: {name}")

# ---------------- DELETE ----------------

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.replace("/delete ", "")

    if not text.isdigit():
        await update.message.reply_text("Приклад: /delete 1")
        return

    delete_task_db(int(text))

    await update.message.reply_text("🗑 Видалено")

# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Бот чеклист (SQLite)\n\n"
        "/list - список\n"
        "/add - додати\n"
        "/delete - видалити"
    )

# ---------------- RUN ----------------

def run_bot():

    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("delete", delete_task))
    app.add_handler(CallbackQueryHandler(button))

    print("SQLite bot started!")

    app.run_polling()

Thread(target=run_web).start()
run_bot()
