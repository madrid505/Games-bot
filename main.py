import logging
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from handlers.games_handler import handle_messages, callback_handler
from config import BOT_TOKEN

# إعداد السجلات
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def main():
    # بناء التطبيق باستخدام التوكن
    app = Application.builder().token(BOT_TOKEN).build()

    # إضافة المعالجات (تأكد من استدعاء MessageHandler و filters بشكل صحيح)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("✅ تم تشغيل بوت مونوبولي الملكي بنجاح...")
    app.run_polling()

if __name__ == "__main__":
    main()
