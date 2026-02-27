import logging
import asyncio
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers import handle_messages, callback_handler

# إعداد السجلات (Logs) لمراقبة أداء البوت
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    try:
        # بناء التطبيق مع إعدادات تضمن عدم تكرار الرسائل القديمة عند التشغيل
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # إضافة معالج الرسائل النصية (يشمل الآن الألعاب، البنك، والتفاعل)
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
        
        # إضافة معالج الأزرار (القائمة الملكية)
        app.add_handler(CallbackQueryHandler(callback_handler))

        print("🚀 [النظام الملكي]: البوت يعمل الآن بكامل طاقته ومقسّم باحترافية...")
        
        # التشغيل بنظام Polling المستقر
        # drop_pending_updates=True تضمن أن البوت لا يرد على الرسائل القديمة التي أُرسلت وهو مطفأ
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ خطأ فادح في تشغيل البوت: {e}")

if __name__ == '__main__':
    main()
