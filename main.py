import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers.games_handler import handle_messages, callback_handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # معالج الرسائل العادية (الألعاب، البنك، الروليت)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
    
    # معالج الأزرار
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("👑 البوت شغال بكامل طاقته الملكية يا Anas!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
