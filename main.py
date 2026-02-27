import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from handlers.games_handler import handle_messages, callback_handler

# إعداد السجلات (للمراقبة في Northflank)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    # تعديل جلب التوكن ليطابق ملف config الخاص بك
    bot_token = config.BOT_TOKEN 
    
    if not bot_token:
        print("❌ خطأ: لم يتم العثور على BOT_TOKEN في ملف config.py")
        return

    application = ApplicationBuilder().token(bot_token).build()

    # 1. تفعيل الأزرار (هذا ما كان ينقصك لتشغيل أزرار القائمة)
    application.add_handler(CallbackQueryHandler(callback_handler))

    # 2. تفعيل النصوص (لتشغيل الألعاب بالكتابة + أوامر البنك + الروليت)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("👑 نظام مونوبولي الملكي استعد للعمل...")
    application.run_polling()

if __name__ == '__main__':
    main()
