import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from db import get_user_data, db, User
import handlers.roulette_handler as roulette
import handlers.games_handler as games
import handlers.bank_handler as bank

logging.basicConfig(level=logging.INFO)

async def global_handler(update, context):
    if not update.message or not update.message.text: return
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # ⭐ ملك التفاعل (مدمج لضمان العمل)
    u_data = await get_user_data(update)
    db.update({'msg_count': u_data.get('msg_count', 0) + 1}, User.id == u_id)

    # 1. الروليت
    if await roulette.handle_roulette(update, context, text, u_id, u_name): return
    # 2. البنك (نسخة Anas: راتب 30 د، ضريبة Anas، حظ عشوائي)
    if await bank.handle_bank(update, context, text, u_name, u_id): return
    # 3. الألعاب (نصوص + إجابات)
    if await games.handle_game_logic(update, context, text): return

    # قائمة الأوامر
    if text in ["الاوامر", "قائمة"]:
        await update.message.reply_text("👑 قائمة أوامر مونوبولي", reply_markup=games.get_main_menu_keyboard())

def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(games.callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_handler))
    print("🚀 تم استعادة النسخة المستقرة بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
