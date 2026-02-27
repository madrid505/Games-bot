import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters

# استيراد الوحدات المنفصلة بمسارات مباشرة لتجنب مشاكل الاستيراد
import handlers.interaction_handler as interaction
import handlers.roulette_handler as roulette
import handlers.games_handler as games
import handlers.bank_handler as bank

# إعداد السجلات لمراقبة أداء البوت في Northflank
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

async def global_handler(update, context):
    """
    الموزع العالمي: يستقبل كل رسالة نصية ويقرر أين يرسلها بالترتيب.
    """
    # التأكد من أن الرسالة تحتوي على نص ومن مجموعة مسموحة
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # 1️⃣ ملك التفاعل: (يعمل أولاً مع كل رسالة لزيادة العداد)
    await interaction.update_interaction(update, u_id)

    # 2️⃣ الروليت: (يفحص إذا كان النص 'انا' أو 'روليت')
    if await roulette.handle_roulette(update, context, text, u_id, u_name):
        return

    # 3️⃣ الألعاب بالنصوص: (يفحص إذا كان النص اسم لعبة أو إجابة صحيحة)
    if await games.handle_game_logic(update, context, text):
        return

    # 4️⃣ أوامر البنك: (زرف، راتب، رصيدي...)
    if await bank.handle_bank(update, context, text, u_name, u_id):
        return

    # 5️⃣ قائمة الأوامر:
    if text in ["الاوامر", "قائمة", "الأوامر"]:
        await update.message.reply_text(
            "👑 **مرحباً بك في عالم مونوبولي الملكي**\n\nاختر اللعبة من الأزرار أدناه أو اكتب اسمها مباشرة:", 
            reply_markup=games.get_main_menu_keyboard()
        )

def main():
    # التحقق من وجود التوكن
    if not hasattr(config, 'BOT_TOKEN'):
        print("❌ خطأ: لم يتم العثور على BOT_TOKEN في config.py")
        return

    # بناء التطبيق باستخدام التوكن الخاص بك
    application = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # [حل مشكلة الأزرار]: ربط معالج الأزرار بالدالة المخصصة لها
    application.add_handler(CallbackQueryHandler(games.callback_handler))

    # [حل مشكلة النصوص]: ربط الموزع العالمي بكل الرسائل النصية
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_handler))

    print("🚀 تم تشغيل نظام مونوبولي الملكي (إصدار الوحدات المنفصلة)...")
    application.run_polling()

if __name__ == '__main__':
    main()
