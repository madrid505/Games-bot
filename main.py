import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from handlers.games_handler import handle_messages, callback_handler

# إعداد السجلات لمراقبة البوت في Northflank
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    # استخدام BOT_TOKEN كما هو في ملف config.py الخاص بك
    bot_token = config.BOT_TOKEN 
    
    if not bot_token:
        print("❌ خطأ: لم يتم العثور على BOT_TOKEN في ملف config.py")
        return

    application = ApplicationBuilder().token(bot_token).build()

    # [حل مشكلة الأزرار]: هذا السطر هو المسؤول عن جعل الأزرار تستجيب عند الضغط
    application.add_handler(CallbackQueryHandler(callback_handler))

    # [حل مشكلة نصوص الألعاب وملك التفاعل]: هذا السطر يوجه كل نص إلى الدالة المسؤولة
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("👑 نظام مونوبولي الملكي يعمل بكامل طاقته الآن...")
    application.run_polling()

if __name__ == '__main__':
    main()
