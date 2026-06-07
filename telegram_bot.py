import os
import re
import time
import requests
from flask import Flask, request
from database.db import add_user, log_query, get_stats, get_all_users, get_logs

app = Flask(__name__)
TOKEN = os.environ.get("TELEGRAM_BOT_API_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "").split(","))) if os.environ.get("ADMIN_IDS") else []

def escape_markdown(text):
    if not text:
        return text
    return str(text).replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]").replace("`", "\\`")

def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{API}/sendMessage", json=payload, timeout=10)

def fetch_data(number):
    try:
        url = f"https://exploitsindia.site/track/live.php?term={number}"
        res = requests.get(url, timeout=10).text
        def get(pattern):
            m = re.search(pattern, res)
            return m.group(1).strip() if m else "N/A"
        return {"name": get(r"Name[:\-]?\s*(.*)"), "mobile": number, "address": get(r"Address[:\-]?\s*(.*)")}
    except Exception as e:
        print(f"fetch_data error: {e}")
        return None

def is_admin(user_id):
    return user_id in ADMIN_IDS

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return {"ok": False}
    
    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]
        user_id = msg.get("from", {}).get("id")
        text = msg.get("text", "")
        
        if text == "/start":
            add_user(user_id, msg.get("from", {}).get("username"), msg.get("from", {}).get("first_name"))
            keyboard = {"keyboard": [["🔍 Lookup"], ["ℹ️ About", "📞 Support"]], "resize_keyboard": True}
            send_message(chat_id, "🤖 *MADDY ASSISTANT*\n\nFast • Reliable • Secure\n\nChoose an option:", reply_markup=keyboard)
        
        elif text in ["🔍 Lookup", "/lookup"]:
            send_message(chat_id, "🔍 Send the phone number to lookup:")
        
        elif text in ["ℹ️ About", "/about"]:
            send_message(chat_id, "ℹ️ *About*\n\nProfessional phone lookup bot\nVersion 2.0\n\nEducational Purpose Only")
        
        elif text in ["📞 Support", "/support"]:
            send_message(chat_id, "📞 *Support*\n\nContact: @Maadhu\nIssues: github.com/Maadhu938\n\nUser is responsible for their messages")
        
        elif text in ["📊 Stats", "/stats"] and is_admin(user_id):
            users, total, today = get_stats()
            send_message(chat_id, f"📊 *Statistics*\n\nUsers: {users}\nRequests: {total}\nToday: {today}")
        
        elif text in ["👥 Users", "/users"] and is_admin(user_id):
            users = get_all_users()
            text_out = "👥 *Users*\n\n"
            for uid, username, name in users[:20]:
                text_out += f"ID: `{uid}` | @{escape_markdown(username or 'N/A')} | {escape_markdown(name or 'N/A')}\n"
            send_message(chat_id, text_out)
        
        elif text in ["📝 Logs", "/logs"] and is_admin(user_id):
            logs = get_logs()
            text_out = "📝 *Recent Logs*\n\n"
            for uid, query, ts in logs[:20]:
                text_out += f"`{ts}` | `{uid}` | {query}\n"
            send_message(chat_id, text_out or "No logs yet")
        
        elif text.startswith("/broadcast") and is_admin(user_id):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                send_message(chat_id, "Usage: /broadcast <message>")
                return {"ok": True}
            msg_text = parts[1]
            sent = 0
            for uid, _, _ in get_all_users():
                try:
                    requests.post(f"{API}/sendMessage", json={"chat_id": uid, "text": msg_text, "parse_mode": "Markdown"}, timeout=10)
                    sent += 1
                    time.sleep(0.05)
                except Exception as e:
                    print(f"Broadcast error to {uid}: {e}")
            send_message(chat_id, f"📢 Sent to {sent} users")
        
        elif text == "/admin" and is_admin(user_id):
            keyboard = {"keyboard": [["📊 Stats", "👥 Users"], ["📝 Logs", "📢 Broadcast"]], "resize_keyboard": True}
            send_message(chat_id, "🔧 Admin Panel:", reply_markup=keyboard)
        
        elif isinstance(text, str) and not text.startswith("/"):
            add_user(user_id)
            log_query(user_id, text)
            data_out = fetch_data(text)
            if data_out:
                reply_markup = {"inline_keyboard": [[{"text": "📊 Stats", "callback_data": "stats"}], [{"text": "🔍 New Lookup", "callback_data": "lookup"}]]}
                send_message(chat_id,
                    f"🔍 *Lookup Result*\n\n"
                    f"👤 *Name*\n`{escape_markdown(data_out['name'])}`\n\n"
                    f"📱 *Mobile*\n`{escape_markdown(data_out['mobile'])}`\n\n"
                    f"📍 *Address*\n_{escape_markdown(data_out['address'])}_\n\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"🤖 Developed by Maadhu\n"
                    f"Educational Purpose Only",
                    reply_markup=reply_markup
                )
            else:
                send_message(chat_id, "❌ Unable to fetch data. Please try again.")
    
    elif "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        data_cb = query["data"]
        
        if data_cb == "stats":
            users, total, today = get_stats()
            requests.post(f"{API}/editMessageText", json={"chat_id": chat_id, "message_id": query["message"]["message_id"],
                "text": f"📊 *Stats*\n\nUsers: {users}\nRequests: {total}\nToday: {today}\n\nEducational Purpose Only", "parse_mode": "Markdown"}, timeout=10)
        elif data_cb == "lookup":
            requests.post(f"{API}/editMessageText", json={"chat_id": chat_id, "message_id": query["message"]["message_id"],
                "text": "🔍 Send the phone number to lookup:"}, timeout=10)
        requests.post(f"{API}/answerCallbackQuery", json={"callback_query_id": query["id"]}, timeout=10)
    
    return {"ok": True}

@app.route("/", methods=["GET"])
def health():
    return "Bot is running"

if __name__ == "__main__":
    app.run()