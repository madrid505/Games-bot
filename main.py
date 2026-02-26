import logging
import asyncio
import sys
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from handlers.games_handler import handle_messages, callback_handler
from config import BOT_TOKEN

# إعداد السجلات
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def run_bot():
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        
        # إضافة المعالجات (التأكد من رتبة الفلاتر)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
        app.add_handler(CallbackQueryHandler(callback_handler))

        print("✅ تم تشغيل بوت مونوبولي الملكي بنجاح...")
        
        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            # إبقاء البوت يعمل للأبد
            while True:
                await asyncio.sleep(3600)
    except Exception as e:
        print(f"❌ خطأ فادح في التشغيل: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 تم إيقاف البوت.")
