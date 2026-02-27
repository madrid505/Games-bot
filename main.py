import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters

# استيراد الوظائف من الملفات المنفصلة
from handlers.interaction_handler import update_interaction
from handlers.roulette_handler import handle_roulette
from handlers.games_handler import handle_game_logic, callback_handler, get_main_menu_keyboard
from handlers.bank_handler import handle_bank

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def global_handler(update, context):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # ✅ 1. ملك التفاعل: يعمل مع كل رسالة (تحديث العداد)
    await update_interaction(update, u_id)

    # ✅ 2. الروليت: (فحص "انا" أو "روليت")
    if await handle_roulette(update, context, text, u_id, u_name):
        return

    # ✅ 3. الألعاب بالنصوص: (فحص اسم اللعبة أو الإجابة)
    if await handle_game_logic(update, context, text):
        return

    # ✅ 4. أوامر البنك: (زرف، راتب، حظ...)
    # ملاحظة: نمرر context لضمان عمل الزرف والردود
    if await handle_bank(update, context, text, u_name, u_id):
        return

    # ✅ 5. قائمة الأوامر
    if text in ["الاوامر", "قائمة", "الأوامر"]:
        await update.message.reply_text("👑 **قائمة أوامر مونوبولي الملكي**", reply_markup=get_main_menu_keyboard())

def main():
    if not hasattr(config, 'BOT_TOKEN'):
        print("❌ خطأ: BOT_TOKEN غير موجود في config.py")
        return

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # معالج الأزرار
    app.add_handler(CallbackQueryHandler(callback_handler))

    # معالج النصوص الشامل
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_handler))

    print("🚀 تم تشغيل النظام الملكي بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
