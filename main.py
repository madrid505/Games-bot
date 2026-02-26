import logging
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from handlers import register_handlers

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8613134391:AAEfV8sqV7_Kh5g9KG5xT8S9mwl0eqVxFBI"

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    register_handlers(app)
    app.run_polling()

if __name__ == "__main__":
    main()
