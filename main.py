import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from handlers.interaction_handler import update_interaction
from handlers.roulette_handler import handle_roulette
from handlers.games_handler import handle_game_logic, callback_handler, get_main_menu_keyboard
from handlers.bank_handler import handle_bank

async def global_handler(update, context):
    if not update.message or not update.message.text: return
    
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # 1. ملك التفاعل (يعمل مع كل رسالة أولاً)
    await update_interaction(update, u_id)

    # 2. الروليت
    if await handle_roulette(update, context, text, u_id, u_name): return

    # 3. الألعاب (نصوص)
    if await handle_game_logic(update, context, text): return

    # 4. البنك (زرف، راتب..)
    if await handle_bank(update, None, text, u_name, u_id): return

    # 5. القائمة
    if text in ["الاوامر", "قائمة"]:
        await update.message.reply_text("👑 قائمة الأوامر:", reply_markup=get_main_menu_keyboard())

def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
