import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers import handle_messages, callback_handler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    try:
        # بناء التطبيق
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # إضافة المعالجات
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
        app.add_handler(CallbackQueryHandler(callback_handler))

        print("✅ تم تشغيل نظام مونوبولي الملكي بنجاح...")
        
        # التشغيل بنظام Polling المستقر
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ حدث خطأ في التشغيل: {e}")

if __name__ == '__main__':
    main()
