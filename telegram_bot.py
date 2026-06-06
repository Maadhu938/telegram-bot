import os
import re
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

app = Flask(__name__)
bot_app = None


def fetch_data(number):
    try:
        url = f"https://exploitsindia.site/track/live.php?term={number}"
        res = requests.get(url, timeout=10).text

        def get(pattern):
            m = re.search(pattern, res)
            return m.group(1).strip() if m else "N/A"

        return {
            "name": get(r"Name[:\-]?\s*(.*)"),
            "mobile": number,
            "address": get(r"Address[:\-]?\s*(.*)")
        }
    except:
        return None


async def start(update: Update, context):
    await update.message.reply_text('Welcome to HACKER TRACKER! Please enter the target number:')


async def handle_message(update: Update, context):
    number = update.message.text
    data = fetch_data(number)
    if data:
        response = (
            f"\u26a1 TARGET INFORMATION \u26a1\n\n"
            f"\ud83d\udc64 NAME : {data['name']}\n\n"
            f"\ud83d\udcf1 MOBILE : {data['mobile']}\n\n"
            f"\ud83d\udccd LOCATION : {data['address']}"
        )
    else:
        response = "Unable to fetch data. Please try again."
    await update.message.reply_text(response)


@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), bot_app.bot)
    import asyncio
    asyncio.run(bot_app.process_update(update))
    return "OK"


@app.route("/", methods=["GET"])
def health():
    return "Bot is running"


def init_bot():
    global bot_app
    token = os.getenv("TELEGRAM_BOT_API_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_API_TOKEN not set")
    bot_app = ApplicationBuilder().token(token).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


init_bot()
