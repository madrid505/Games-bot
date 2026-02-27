import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from config import TOKEN
from handlers.games_handler import handle_messages, callback_handler # تأكد من استيراد callback_handler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    # بناء التطبيق
    application = ApplicationBuilder().token(TOKEN).build()

    # 1. معالج الأزرار (ضروري جداً لكي تعمل أزرار الألعاب)
    application.add_handler(CallbackQueryHandler(callback_handler))

    # 2. معالج النصوص (لكي تعمل الألعاب بالكتابة وأوامر البنك)
    # نستخدم filters.TEXT لضمان استقبال كل النصوص
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("👑 بوت مونوبولي الملكي يعمل الآن...")
    application.run_polling()

if __name__ == '__main__':
    main()
