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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "-1000000000"))
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "0xYOURADDRESS").strip()
POST_INTERVAL_SECONDS = 12600

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("stoopid_agent")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.getenv("PORT", "10000"))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

recent = defaultdict(lambda: deque(maxlen=20))

def pick(name, lines):
    pool = [l for l in lines if l not in recent[name]]
    choice = random.choice(pool if pool else lines)
    recent[name].append(choice)
    return choice

welcome_lines = [
    "Welcome to STOOPID R1CH. Don’t be broke in here.",
    "New member detected. Wallet unknown. Confidence fake.",
    "You made it in. Try not to fumble your bags.",
    "Welcome to STOOPID R1CH, where bad decisions wear designer labels.",
    "Another degen just walked in like he knows something.",
    "Congrats, you found the rich side of stupid.",
    "Welcome in. Leave the weak hands at the door.",
    "New arrival. Somebody hide the exit liquidity.",
    "You’re in now. Don’t act poor.",
    "Welcome to the mansion, degen. Don’t touch nothing.",
    "Another bag chaser entered the building.",
    "You made it. Now try not to buy tops for sport.",
    "Fresh meat in the money pit.",
    "Welcome to STOOPID R1CH. We clown hard and count harder.",
    "New member joined. Net worth under review.",
    "If you came here to be sensible, wrong room.",
    "Welcome in. Broke energy gets roasted on sight.",
    "Another future liquidity provider has arrived.",
    "You’re officially inside the stupidest rich room on Telegram.",
    "Welcome. Keep your jokes sharp and your bags sharper.",
    "New user detected. Let’s see if your wallet got hands or excuses.",
    "Welcome to the penthouse, peasant.",
    "Another degen climbed through the gate.",
    "You’re in. Act like your portfolio has potential.",
    "Welcome. No crying over red candles unless it’s funny.",
    "Another reckless investor has entered the villa.",
    "You found STOOPID R1CH. That was the smart part.",
    "Welcome in. Everything from here gets louder and richer.",
    "New member. Somebody get him a fake sense of conviction.",
    "Another clown with a dream and a wallet joined.",
    "You made it to the rich side of bad judgment.",
    "Welcome. We respect money, memes, and absolutely nothing else.",
    "New arrival logged. Swagger pending.",
    "Welcome in. Keep it rude, rich, and ridiculously on-chain.",
    "Another bag addict entered the chat.",
    "You’re in. Don’t ask dumb questions unless they’re funny.",
    "Welcome to STOOPID R1CH, where taste is optional and gains are spiritual.",
    "New member just walked in like rent isn’t due.",
    "Welcome. If you’re scared, fake confidence like the rest.",
    "Another degen entered the mansion in dirty Crocs.",
    "You’re in now. Try not to embarrass your wallet.",
    "Fresh arrival. Somebody explain money without sounding poor.",
    "Welcome to STOOPID R1CH. Broke vibes get bullied here.",
    "Another self-appointed market genius has joined.",
    "You made it. The chart still hates you though.",
    "Welcome. Rich mouth, reckless habits, perfect fit.",
    "Another money goblin entered the ballroom.",
    "You got in. That already puts you ahead of some people.",
    "Welcome in. Don’t trip over your own hopium.",
    "New user. Let’s see if you’re rich or just loud.",
    "Welcome to the house of bad influence and bigger dreams.",
    "Another bag romantic entered the premises.",
    "You’re here now. Keep the delusion luxurious.",
    "Welcome. If you lose money, at least be entertaining.",
    "Another candle worshipper has arrived.",
    "Welcome to STOOPID R1CH. We do classless wealth perfectly.",
    "You joined. Great. Now don’t type like a peasant.",
    "New member detected. Sauce level unknown.",
    "Welcome. You can be dumb, just be profitable.",
    "Another portfolio victim has entered the lounge.",
    "You made it in. Now pretend you belong in a mansion.",
    "Welcome to STOOPID R1CH. We laugh first, buy second, regret later.",
    "New user entered. Somebody loan him an ego.",
    "Welcome. Bring money talk or bring jokes.",
    "Another overconfident chart reader joined.",
    "You’re inside now. Keep it expensive and unnecessary.",
    "Welcome in. This is where rich nonsense lives.",
    "New member. Somebody check if he’s all cap.",
    "Another bagholder with ambition just showed up.",
    "Welcome. Here we flex delusion like it’s luxury.",
    "You got in. Please keep the poverty-stricken takes outside.",
    "Another degen wandered into wealth cosplay.",
    "Welcome to STOOPID R1CH, home of premium bad ideas.",
    "You made it. Don’t make us regret approving your aura.",
    "Fresh member. Somebody hand him some imaginary alpha.",
    "Welcome. Be funny, be rude, be up.",
    "Another gambler with confidence issues arrived.",
    "You’re in. Now talk like your wallet has a balcony.",
    "Welcome to the room where even the jokes wear chains.",
    "New member detected. Hype level pending verification.",
    "Another one entered thinking this was a support group.",
    "Welcome in. This is not therapy. This is STOOPID R1CH.",
    "You joined. That was brave for someone with your candle history.",
    "Another dream-chasing lunatic stepped inside.",
    "Welcome. Keep the bag talk filthy rich.",
    "New user in the building. Hide your tops.",
    "Another luxury-level degen has landed.",
    "Welcome to STOOPID R1CH. If you’re broke, lie better.",
    "You’re here now. Don’t post like your rent is due tomorrow.",
    "Another moon addict entered the foyer.",
    "Welcome. Money over manners, always.",
    "New arrival. Somebody get him a fake Rolex and a real meme.",
    "Another chart goblin joined the party.",
    "Welcome to STOOPID R1CH. We’re elegant in the worst possible way.",
    "You made it inside. Let’s see if your portfolio deserves shoes.",
    "Another loud wallet whisperer arrived.",
    "Welcome. Rich jokes only, broke excuses never.",
    "New member. We’ll decide later if you’re worth the bandwidth.",
    "Another digital gremlin just entered the estate.",
    "Welcome in. Keep it STOOPID, keep it R1CH.",
    "One more degen in the mansion. Terrific.",
    "Another bag enthusiast has entered with suspicious confidence.",
    "Welcome. May your jokes hit harder than your entries.",
    "New member joined. Somebody fluff his ego and check his chart.",
    "You’re in now. Try not to smell like exit liquidity.",
]

money_lines = [
    "💰 detected. Broke people getting nervous.",
    "💰 entered chat. Standards dropped, greed rose.",
    "💰 seen. Somebody’s acting rich again.",
    "💰 in the room. Hide the fake alpha.",
    "💰 spotted. Wallet energy getting disrespectful.",
    "💰 detected. Time to talk reckless and expensive.",
    "💰 just landed. Degens smiling for no reason.",
    "💰 showed up. Poverty excuses not accepted.",
    "💰 energy strong. Bad decisions loading.",
    "💰 entered. Mansion talk activated.",
] * 10

dollar_lines = [
    "$ detected. Degens assembling.",
    "$ seen. Ticker brain activated.",
    "$ just dropped in. Everybody acting like a genius.",
    "$ entered the room. Confidence now overpriced.",
    "$ detected. Somebody about to say generational.",
    "$ seen. Delusion getting funded.",
    "$ entered chat. Net worth roleplay increasing.",
    "$ sighting confirmed. Bags out, brains off.",
    "$ activated. Watch the fools get brave.",
    "$ seen. This room just got louder and poorer mentally.",
] * 10

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
    "Your entry looked personal. The chart took offense.",
    "Everybody wants wealth. Nobody wants patience.",
    "The candle moved 3% and now he’s a macro expert.",
    "The market heard your plan and laughed immediately.",
    "That wasn’t a dip buy. That was emotional damage.",
    "Your portfolio got hands? Because you clearly don’t.",
    "Bulls posting through trauma again.",
    "One more bad entry and you qualify as modern art.",
] * 5

ca_lines = [f"CA:\n{CONTRACT_ADDRESS}"] * 100

news_lines = [
    "NEWS MODE: not wired to live feeds yet, but the money vibe remains active.",
    "No live news feed yet. Rich nonsense still operational.",
    "News mode placeholder. Market still ugly, jokes still premium.",
    "No external news source plugged in. Mansion vibes continue.",
    "News brain sleeping. Swagger still online.",
] * 20

trivia_lines = [
    "TRIVIA: what command spits the CA?",
    "TRIVIA: what symbol wakes up bag talk faster, $ or 💰?",
    "TRIVIA: which mode isn’t live yet, tasks or jokes?",
    "TRIVIA: what command gives chat ID?",
    "TRIVIA: who’s richer, the loudest guy or the smartest one?",
] * 20

task_lines = [
    "TASKS not active yet.",
    "Tasks disabled for now. Rich laziness only.",
    "Task brain sleeping. Come back later.",
    "Tasks ain’t live. Stop rushing greatness.",
    "Tasks mode is parked for now.",
] * 20

auto_lines = [
    "SYSTEM LOG // STOOPID R1CH signal active",
    "SYSTEM LOG // mansion energy unstable",
    "SYSTEM LOG // weak hands remain visible",
    "SYSTEM LOG // bag pressure increasing",
    "SYSTEM LOG // rich nonsense detected",
    "SYSTEM LOG // degen confidence rising",
    "SYSTEM LOG // liquidity fantasies active",
    "SYSTEM LOG // premium delusion online",
    "SYSTEM LOG // money smell in the air",
    "SYSTEM LOG // expensive bad ideas loading",
] * 10

def handle(text):
    t = text.lower()
    if "💰" in text:
        return pick("money", money_lines)
    if "$" in text:
        return pick("dollar", dollar_lines)
    if "joke" in t or "roast" in t or "funny" in t:
        return pick("jokes", jokes)
    if "ca" in t or "contract" in t or "address" in t:
        return pick("ca", ca_lines)
    if "news" in t or "update" in t or "status" in t:
        return pick("news", news_lines)
    if "trivia" in t:
        return pick("trivia", trivia_lines)
    if "task" in t:
        return pick("tasks", task_lines)
    return None

async def welcome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for _member in update.message.new_chat_members:
            await update.message.reply_text(pick("welcome", welcome_lines))

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("STOOPID AGENT ONLINE.")

async def ca_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("ca_cmd", ca_lines))

async def joke_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("joke_cmd", jokes))

async def news_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("news_cmd", news_lines))

async def trivia_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("trivia_cmd", trivia_lines))

async def tasks_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(pick("tasks_cmd", task_lines))

async def id_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(str(update.effective_chat.id))

async def reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        r = handle(update.message.text)
        if r:
            await update.message.reply_text(r)

async def auto_post_loop(app):
    await asyncio.sleep(20)
    while True:
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=pick("auto", auto_lines))
        await asyncio.sleep(POST_INTERVAL_SECONDS)

async def post_init(app):
    log.info("Starting background tasks")
    asyncio.create_task(auto_post_loop(app))

async def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")

    threading.Thread(target=start_health_server, daemon=True).start()

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("ca", ca_cmd))
    app.add_handler(CommandHandler("joke", joke_cmd))
    app.add_handler(CommandHandler("news", news_cmd))
    app.add_handler(CommandHandler("trivia", trivia_cmd))
    app.add_handler(CommandHandler("tasks", tasks_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    log.info("STOOPID AGENT ACTIVE")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
