import os
import re
import requests
import json

TOKEN = os.environ.get("TELEGRAM_BOT_API_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"


def send_message(chat_id, text):
    requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text})


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


def handler(event, context):
    path = event.get("path", "/")
    method = event.get("httpMethod", "GET")
    body = event.get("body", "")

    if path == "/" and method == "GET":
        return {"statusCode": 200, "headers": {"Content-Type": "text/plain"}, "body": "Bot is running"}

    if path == "/webhook" and method == "POST":
        data = json.loads(body) if body else {}
        if "message" in data:
            msg = data["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "")
            if text == "/start":
                send_message(chat_id, "Welcome to HACKER TRACKER! Please enter the target number:")
            else:
                fetched = fetch_data(text)
                if fetched:
                    response = (
                        "\u26a1 TARGET INFORMATION \u26a1\n\n"
                        "\ud83d\udc64 NAME : {}\n\n"
                        "\ud83d\udcf1 MOBILE : {}\n\n"
                        "\ud83d\udccd LOCATION : {}"
                    ).format(fetched["name"], fetched["mobile"], fetched["address"])
                else:
                    response = "Unable to fetch data. Please try again."
                send_message(chat_id, response)
        return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps({"ok": True})}

    return {"statusCode": 404, "body": "Not found"}
