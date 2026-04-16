import os
import re
import asyncio
import random
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict, deque

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# ENV
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "-1003451233402"))
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "0xYOURADDRESS").strip()

POST_INTERVAL_SECONDS = 12600  # 3.5 hours

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("stoopid_agent")

# =========================
# HEALTH SERVER FOR RENDER
# =========================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"STOOPID AGENT OK")

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    log.info("Health server listening on port %s", port)
    server.serve_forever()

# =========================
# LIBRARIES
# =========================
recent_lines = defaultdict(lambda: deque(maxlen=8))

def pick_line(bucket_name, lines):
    recent = recent_lines[bucket_name]
    pool = [line for line in lines if line not in recent]
    choice = random.choice(pool if pool else lines)
    recent.append(choice)
    return choice

start_lines = [
    "STOOPID AGENT ONLINE.",
    "STOOPID AGENT booted up.",
    "Signal live. Brain crooked.",
    "Agent loaded. Logic unstable.",
]

money_lines = [
    "💰 detected. Greed levels rising.",
    "Money signal seen.",
    "Bag talk noticed.",
    "Dollar energy entered the room.",
    "Liquidity lust detected.",
    "Stoopid money mode active.",
    "The feed smelled money.",
    "Capital pressure rising.",
]

dollar_lines = [
    "$ detected. Degens assembling.",
    "Dollar sign seen. Spirits lifted.",
    "$ entered chat. IQ dropped.",
    "Ticker energy confirmed.",
    "The signal likes dollar signs.",
    "Market delusion increasing.",
    "One symbol. Infinite bad decisions.",
    "Bag vision activated.",
]

jokes = [
    "Weak hands detected.",
    "Somebody bought the top with confidence.",
    "Retail woke up exactly on time to be late.",
    "Support is held together by denial.",
    "One green candle and everybody becomes a prophet.",
    "The chart blinked and they called it a breakout.",
    "The signal was there. The spine was not.",
    "Paper hands writing fiction again.",
    "Hopium levels remain reckless.",
    "The bag is heavy because the conviction is fake.",
    "Price moved sideways and six gurus found meaning.",
    "That wasn’t alpha. That was caffeine.",
]

ca_lines = [
    f"CA:\n{CONTRACT_ADDRESS}",
    f"CONTRACT ADDRESS:\n{CONTRACT_ADDRESS}",
    f"Signal requested. CA:\n{CONTRACT_ADDRESS}",
    f"Locked address:\n{CONTRACT_ADDRESS}",
]

news_lines = [
    "NEWS MODE: not plugged into live X news right now. I can still drop vibe updates.",
    "No live news feed connected. Use /news for random system updates for now.",
    "News brain is placeholder mode right now.",
    "No external news source connected yet. Fake calm remains active.",
]

update_lines = [
    "SYSTEM LOG // attention pockets forming",
    "SYSTEM LOG // weak hands remain visible",
    "SYSTEM LOG // timeline distortion rising",
    "SYSTEM LOG // static levels elevated",
    "SYSTEM LOG // meme pressure increasing",
    "SYSTEM LOG // conviction scan unstable",
    "SYSTEM LOG // signal still active",
    "SYSTEM LOG // operator patience low",
]

trivia_lines = [
    "TRIVIA: What command gives the contract address?",
    "TRIVIA: Which symbol wakes up bag energy faster: $ or 💰 ?",
    "TRIVIA: What mode is not active yet: tasks or jokes?",
    "TRIVIA: What command gives your chat ID?",
    "TRIVIA: Which command triggers system-style updates?",
]

task_lines = [
    "TASKS mode is not active yet.",
    "Tasks are disabled for now.",
    "Task brain sleeping. Not live yet.",
    "Tasks coming later. Not wired in now.",
]

fallback_replies = [
    "Signal received.",
    "Observed.",
    "Noted.",
    "Stoopid Agent saw that.",
    "Monitoring.",
    "The feed remembers.",
    "Response accepted.",
    "Degeneracy acknowledged.",
]

# =========================
# KEYWORD LOGIC
# =========================
def get_keyword_reply(raw_text):
    text = raw_text.lower()

    if "💰" in raw_text:
        return pick_line("money", money_lines)

    if "$" in raw_text:
        return pick_line("dollar", dollar_lines)

    if re.search(r"\b(joke|funny|roast)\b", text):
        return pick_line("jokes", jokes)

    if re.search(r"\b(ca|contract|address)\b", text):
        return pick_line("ca", ca_lines)

    if re.search(r"\b(news|update|status)\b", text):
        return pick_line("news", news_lines)

    if re.search(r"\b(trivia)\b", text):
        return pick_line("trivia", trivia_lines)

    if re.search(r"\b(tasks|task)\b", text):
        return pick_line("tasks", task_lines)

    return None

# =========================
# COMMANDS
# =========================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_line("start", start_lines))

async def ca_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_line("ca_cmd", ca_lines))

async def joke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_line("joke_cmd", jokes))

async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_line("news_cmd", news_lines))

async def trivia_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_line("trivia_cmd", trivia_lines))

async def tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick_line("tasks_cmd", task_lines))

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(str(update.effective_chat.id))

async def keyword_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    raw = update.message.text.strip()
    reply = get_keyword_reply(raw)

    if reply:
        await update.message.reply_text(reply)

# =========================
# AUTO POST
# =========================
async def auto_post_loop(app):
    log.info("Starting auto-post loop")
    await asyncio.sleep(20)

    while True:
        msg = pick_line("auto_post", update_lines)
        try:
            await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        except Exception as e:
            log.warning("Auto-post failed: %s", e)

        await asyncio.sleep(POST_INTERVAL_SECONDS)

async def post_init(app):
    log.info("Starting background tasks")
    asyncio.create_task(auto_post_loop(app))

# =========================
# MAIN
# =========================
def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")

    threading.Thread(target=start_health_server, daemon=True).start()

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("ca", ca_cmd))
    app.add_handler(CommandHandler("joke", joke_cmd))
    app.add_handler(CommandHandler("news", news_cmd))
    app.add_handler(CommandHandler("trivia", trivia_cmd))
    app.add_handler(CommandHandler("tasks", tasks_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, keyword_reply))

    log.info("STOOPID AGENT ACTIVE")
  import asyncio

async def main():
    print("STOOPID AGENT ACTIVE")
    await app.run_polling()

if name == "main":
    asyncio.run(main())  
