# main.py
import logging
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from handlers.games_handler import handle_messages, callback_handler
from config import BOT_TOKEN

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("✅ البوت يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == "__main__":
    main()
