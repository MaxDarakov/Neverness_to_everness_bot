import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

print("PTB version:", telegram.__version__)

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("❌ TOKEN не знайдено!")
    raise RuntimeError("Environment variable TOKEN is not set!")
else:
    print("✅ TOKEN знайдено, довжина:", len(TOKEN))

# Хендлер для /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот працює! ✅")

# Запуск бота в окремому потоці
def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("🚀 Запускаю Telegram‑бота...")
    app.run_polling()

# Фіктивний веб‑сервер для Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_server():
    port = int(os.getenv("PORT", 10000))  # Render задає PORT автоматично
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🌐 Web server запущено на порті {port}")
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    run_server()
