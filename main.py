import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters

# استيراد الموزعين من مجلد handlers
# تأكد أن مجلد handlers يحتوي على ملف __init__.py فارغ أو فيه الاستيرادات
import handlers.interaction_handler as interaction
import handlers.roulette_handler as roulette
import handlers.games_handler as games
import handlers.bank_handler as bank

# إعدادات اللوج لمراقبة الأداء في Northflank
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

async def global_handler(update, context):
    """
    الموزع الرئيسي: يقوم بتشغيل الوظائف بالترتيب الصحيح.
    """
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # 1️⃣ ملك التفاعل: تحديث العداد فوراً مع كل رسالة
    await interaction.update_interaction(update, u_id)

    # 2️⃣ الروليت: فحص أوامر الروليت (انا، روليت، تم)
    if await roulette.handle_roulette(update, context, text, u_id, u_name):
        return

    # 3️⃣ البنك الملكي: (راتب، حظ، رصيدي) - نسخة Anas المعدلة
    if await bank.handle_bank(update, context, text, u_name, u_id):
        return

    # 4️⃣ الألعاب: فحص إذا كان النص اسم لعبة أو إجابة
    if await games.handle_game_logic(update, context, text):
        return

    # 5️⃣ قائمة الأوامر
    if text in ["الاوامر", "قائمة", "الأوامر"]:
        await update.message.reply_text(
            "👑 **مرحباً بك في عالم مونوبولي الملكي**\n\nاختر اللعبة من الأزرار أو اكتب اسمها مباشرة:", 
            reply_markup=games.get_main_menu_keyboard()
        )

def main():
    if not hasattr(config, 'BOT_TOKEN'):
        print("❌ خطأ: BOT_TOKEN غير موجود في ملف config.py")
        return

    # بناء التطبيق
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # معالج ضغطات الأزرار (Callbacks)
    app.add_handler(CallbackQueryHandler(games.callback_handler))

    # معالج النصوص الشامل (الموزع)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_handler))

    print("🚀 تم تشغيل المحرك الرئيسي بنجاح... (نظام Anas الملكي)")
    app.run_polling()

if __name__ == '__main__':
    main()
