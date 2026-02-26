import asyncio
import logging
from telegram.ext import Application
from handlers import register_handlers
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # استدعاء الدالة التي تسجل كل الملفات الجديدة
    register_handlers(app)

    print("✅ تم تشغيل نظام ميسك المطور (نظام الملفات المنفصلة) بنجاح...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(run_bot())
