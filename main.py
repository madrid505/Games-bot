import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from handlers import update_interaction, handle_messages, callback_handler

logging.basicConfig(level=logging.INFO)

def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    # ربط الأزرار
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # ربط الرسائل (ملك التفاعل + الألعاب + البنك)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    print("🚀 تم العودة للنسخة الذهبية بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
