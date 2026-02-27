import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from handlers.games_handler import handle_messages, callback_handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    bot_token = config.BOT_TOKEN 
    if not bot_token:
        return

    application = ApplicationBuilder().token(bot_token).build()

    # الأزرار أولاً لضمان الاستجابة السريعة
    application.add_handler(CallbackQueryHandler(callback_handler))

    # النصوص ثانياً (تشمل الألعاب، البنك، وملك التفاعل)
    # ملاحظة: handle_messages يجب أن تكون هي المعالج الرئيسي الوحيد للنصوص
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("🚀 تم تشغيل المحرك الملكي بنجاح...")
    application.run_polling()

if __name__ == '__main__':
    main()
