import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers.games_handler import handle_messages, callback_handler

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def catch_ids(update, context):
    # 1. فحص إذا كان هناك رسالة وصورة
    if update.message and update.message.photo:
        try:
            # الحصول على ID الصورة (أعلى دقة)
            photo_id = update.message.photo[-1].file_id
            # إرسال الكود للمستخدم بتنسيق قابل للنسخ
            await update.message.reply_text(
                f"✅ **تم صيد الـ ID بنجاح يا ملك:**\n\n`{photo_id}`\n\nاضغط على الكود لنسخه 👆",
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Error catching ID: {e}")

    # 2. تشغيل الأوامر الطبيعية للبوت (ضروري جداً لعدم توقف البوت)
    await handle_messages(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # المعالج الرئيسي: يدمج الصيد مع الرسائل العادية
    # ملاحظة: filters.ALL تضمن أن أي تفاعل يمر عبر دالة الصيد أولاً
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), catch_ids))
    
    # معالج الأزرار
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("👑 صياد الصور جاهز للعمل الآن..")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
