import config
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from handlers.interaction_handler import update_interaction
from handlers.roulette_handler import handle_roulette
from handlers.games_handler import handle_game_logic, callback_handler, get_main_menu_keyboard
from handlers.bank_handler import handle_bank

logging.basicConfig(level=logging.INFO)

async def global_handler(update, context):
    if not update.message or not update.message.text: return
    
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # 1. ملك التفاعل (يعمل أولاً دائماً مع كل رسالة)
    await update_interaction(update, u_id)

    # 2. الروليت (فحص إذا كان النص "انا" أو "روليت")
    if await handle_roulette(update, context, text, u_id, u_name): return

    # 3. الألعاب (فحص إذا كان النص اسم لعبة أو إجابة)
    if await handle_game_logic(update, context, text): return

    # 4. البنك (زرف، راتب، كنز..)
    if await handle_bank(update, None, text, u_name, u_id): return

    # 5. قائمة الأوامر
    if text in ["الاوامر", "قائمة"]:
        await update.message.reply_text("👑 **عالم مونوبولي الملكي**", reply_markup=get_main_menu_keyboard())

def main():
    # التأكد من استخدام التوكن الصحيح من ملفك
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    # ربط الأزرار
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # ربط كافة النصوص بالموزع العالمي
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_handler))
    
    print("🚀 تم تشغيل البوت بنظام الوحدات المنفصلة...")
    app.run_polling()

if __name__ == '__main__':
    main()
