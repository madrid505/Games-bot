import logging
‏from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
‏from config import BOT_TOKEN
‏from handlers.games_handler import handle_messages, callback_handler
‏
‏# إعداد السجلات (Logs)
‏logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
‏
‏async def catch_ids(update, context):
‏    # 📸 فحص إذا كانت الرسالة تحتوي على صورة
‏    if update.message and update.message.photo:
‏        # أخذ أعلى دقة للصورة للحصول على File ID صحيح
‏        photo_id = update.message.photo[-1].file_id
‏        # الرد بالكود فوراً مع تفعيل خاصية النسخ بلمسة واحدة
‏        await update.message.reply_text(
‏            f"✅ **تم صيد الـ ID بنجاح يا ملك:**\n\n`{photo_id}`\n\nاضغط على الكود أعلاه لنسخه فوراً 👆",
‏            parse_mode='MarkdownV2'
‏        )
‏    
‏    # بعد الصيد، السماح للبوت بإكمال مهامه الطبيعية (ألعاب، رصيد، إلخ)
‏    await handle_messages(update, context)
‏
‏def main():
‏    app = ApplicationBuilder().token(BOT_TOKEN).build()
‏    
‏    # إضافة معالج الصيد (يفحص الصور والنصوص)
‏    # filters.PHOTO: يسمح للصيد بالعمل بمجرد إرسال أي صورة
‏    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & (~filters.COMMAND), catch_ids))
‏    
‏    # معالج الأزرار (القائمة)
‏    app.add_handler(CallbackQueryHandler(callback_handler))
‏    
‏    print("👑 البوت الآن في وضع 'صياد الأكواد'.. ابدأ بإرسال الصور يا Anas!")
‏    app.run_polling(drop_pending_updates=True)
‏
‏if __name__ == '__main__':
‏    main()
‏
