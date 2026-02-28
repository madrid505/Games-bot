import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers.games_handler import handle_messages, callback_handler

# إعداد السجلات (لوج) لضمان متابعة أي أخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def catch_ids(update, context):
    # 1. ميزة صيد الـ ID (للملك والمشرفين لإضافة صور للموسم)
    if update.message and update.message.photo:
        # هنا البوت يصيد الـ File ID لنسخه ووضعه في images.txt أو SEASON_ALBUM
        try:
            photo_id = update.message.photo[-1].file_id
            await update.message.reply_text(
                f"✅ **تم صيد الـ ID بنجاح يا ملك:**\n\n`{photo_id}`\n\nاضغط على الكود لنسخه 👆",
                parse_mode='Markdown'
            )
        except Exception as e:
            logging.error(f"Error catching ID: {e}")

    # 2. تشغيل الأوامر الطبيعية للبوت (البنك، الألعاب، الألبوم، ملك التفاعل)
    await handle_messages(update, context)

def main():
    # بناء تطبيق البوت
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # المعالج الرئيسي: يدمج صيد الصور مع معالجة الرسائل والأوامر
    # ملاحظة: filters.ALL تضمن أن البوت يرى الرسائل النصية والصور
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), catch_ids))
    
    # معالج الأزرار التفاعلية (ضروري جداً لدفتر النتائج، القائمة، ونظام الرجوع)
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("👑 إمبراطورية مونوبولي تعمل الآن بنظام الألبومات والحماية الحديدية..")
    
    # تشغيل البوت وتجاهل الرسائل القديمة عند البدء (drop_pending_updates)
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
