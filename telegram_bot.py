import os
     from telegram import Update, ReplyKeyboardMarkup
     from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
     import requests
     import re

     # Your existing fetch_data function
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

     # Define the start command handler
     def start(update: Update, context: CallbackContext) -> None:
         update.message.reply_text('Welcome to HACKER TRACKER! Please enter the target number:')

     # Define the message handler to fetch and send data
     def handle_message(update: Update, context: CallbackContext) -> None:
         number = update.message.text
         data = fetch_data(number)
         if data:
             response = f"⚡ TARGET INFORMATION ⚡\n\n" \
                        f"👤 NAME : {data['name']}\n\n" \
                        f"📱 MOBILE : {data['mobile']}\n\n" \
                        f"📍 LOCATION : {data['address']}"
             update.message.reply_text(response)
         else:
             update.message.reply_text("Unable to fetch data. Please try again.")

     # Set up the updater and handlers
     def main() -> None:
         # Read the token from environment variables
         token = os.getenv('TELEGRAM_BOT_API_TOKEN')
         if not token:
             raise ValueError("Telegram bot token not found in environment variables")

         updater = Updater(token, use_context=True)
         dispatcher = updater.dispatcher

         dispatcher.add_handler(CommandHandler("start", start))
         dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

         updater.start_polling()
         updater.idle()

     if __name__ == '__main__':
         main()