
import os, re, asyncio, random, logging, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict, deque
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "-1000000000"))
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "0xYOURADDRESS").strip()
POST_INTERVAL_SECONDS = 12600

logging.basicConfig(level=logging.INFO)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def start_health():
    port = int(os.getenv("PORT", "10000"))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

recent = defaultdict(lambda: deque(maxlen=20))

def pick(name, lines):
    pool = [l for l in lines if l not in recent[name]]
    choice = random.choice(pool if pool else lines)
    recent[name].append(choice)
    return choice

def gen(prefix):
    return [f"{prefix} #{i}" for i in range(1,101)]

money = gen("💰 STOOPID R1CH money talk")
dollar = gen("$ STOOPID R1CH bag alert")
jokes = gen("STOOPID R1CH roast mode")
ca = [f"CA:\n{CONTRACT_ADDRESS}"] * 100
news = gen("STOOPID R1CH fake news")
trivia = gen("STOOPID R1CH trivia")
tasks = ["TASKS not active"] * 50
auto_lines = gen("SYSTEM LOG STOOPID R1CH")

def handle(text):
    t = text.lower()
    if "💰" in text: return pick("money", money)
    if "$" in text: return pick("dollar", dollar)
    if "joke" in t: return pick("jokes", jokes)
    if "ca" in t: return pick("ca", ca)
    if "news" in t: return pick("news", news)
    if "trivia" in t: return pick("trivia", trivia)
    if "task" in t: return pick("tasks", tasks)

async def reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message:
        r = handle(update.message.text)
        if r:
            await update.message.reply_text(r)

async def auto(app):
    await asyncio.sleep(20)
    while True:
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=pick("auto", auto_lines))
        await asyncio.sleep(POST_INTERVAL_SECONDS)

async def post_init(app):
    asyncio.create_task(auto(app))

def main():
    threading.Thread(target=start_health, daemon=True).start()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))
    app.run_polling()

if __name__ == "__main__":
    main()
