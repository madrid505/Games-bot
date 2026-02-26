# main.py
import logging
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from handlers import register_handlers
from config import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # تسجيل جميع ال handlers
    register_handlers(app)

    # بدء البوت
    app.run_polling()

if __name__ == "__main__":
    main()
