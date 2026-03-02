import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, OWNER_ID
from handlers.games_handler import handle_messages, callback_handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def catch_ids(update, context):
    if not update.message: return

    # 2. تشغيل الأوامر الطبيعية (البنك، الألعاب، الألبوم) للرسائل النصية
    if update.message.text:
        await handle_messages(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # استخدام filters.ALL لاستقبال الصور والنصوص
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), catch_ids))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("👑 إمبراطورية مونوبولي تعمل الآن بنظام الألبومات والحماية الحديدية..")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
