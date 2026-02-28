import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers.games_handler import handle_messages, callback_handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def catch_ids(update, context):
    if update.message and update.message.photo:
        # هاد السطر رح يطبع الكود في الـ Logs عندك باللون الأحمر عشان تشوفه
        print(f"📸📸 [FILE ID]: {update.message.photo[-1].file_id}")
    await handle_messages(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # تعديل بسيط: خليناه يمر على دالة صيد الأكواد أولاً
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & (~filters.COMMAND), catch_ids))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("👑 البوت شغال وجاهز لصيد الصور يا Anas!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
