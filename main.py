import logging
import asyncio
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers import handle_messages, callback_handler

# إعداد السجلات (Logs)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
        app.add_handler(CallbackQueryHandler(callback_handler))

        # --- الجملة الاختبارية لـ Anas ---
        print("👑 [النظام الملكي]: يا Anas، أنا الآن أعمل بالنسخة الجديدة 2026! 🚀")
        # -------------------------------
        
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح في تشغيل البوت: {e}")

if __name__ == '__main__':
    main()
