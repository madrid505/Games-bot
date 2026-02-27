import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters
from db import get_user_data, db, User

# استيراد الألعاب والبنك والروليت
import handlers.roulette_handler as roulette
import handlers.games_handler as games
import handlers.bank_handler as bank

logging.basicConfig(level=logging.INFO)

async def global_handler(update, context):
    if not update.message or not update.message.text: return
    
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # ⭐ رجعنا ملك التفاعل هنا (بدون ملف خارجي)
    # يحدث العداد فوراً لأي رسالة تدخل القروب
    u_data = await get_user_data(update)
    db.update({'msg_count': u_data.get('msg_count', 0) + 1}, User.id == u_id)

    # 1. الروليت (انا، روليت، تم)
    if await roulette.handle_roulette(update, context, text, u_id, u_name): return

    # 2. البنك الملكي (راتب، حظ، رصيدي)
    if await bank.handle_bank(update, context, text, u_name, u_id): return

    # 3. الألعاب (نصوص الألعاب وفحص الإجابات)
    if await games.handle_game_logic(update, context, text): return

    # 4. قائمة الأوامر
    if text in ["الاوامر", "قائمة", "الأوامر"]:
        await update.message.reply_text(
            "👑 **مرحباً بك في عالم مونوبولي الملكي**",
            reply_markup=games.get_main_menu_keyboard()
        )

def main():
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(games.callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_handler))
    print("🚀 تم تشغيل النسخة الذهبية (ملك التفاعل مدمج)...")
    app.run_polling()

if __name__ == '__main__':
    main()
