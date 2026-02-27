import logging
import config
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters

# استيراد مباشر من الملفات لتجنب مشاكل الـ __init__
import handlers.interaction_handler as interaction
import handlers.roulette_handler as roulette
import handlers.games_handler as games
import handlers.bank_handler as bank

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def global_handler(update, context):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    u_id = update.effective_user.id
    u_name = update.effective_user.first_name

    # 1. ملك التفاعل
    await interaction.update_interaction(update, u_id)

    # 2. الروليت
    if await roulette.handle_roulette(update, context, text, u_id, u_name):
        return

    # 3. الألعاب (نص)
    if await games.handle_game_logic(update, context, text):
        return

    # 4. البنك
    if await bank.handle_bank(update, context, text, u_name, u_id):
        return

    # 5. القائمة
    if text in ["الاوامر", "قائمة", "الأوامر"]:
        await update.message.reply_text("👑 **قائمة أوامر مونوبولي الملكي**", reply_markup=games.get_main_menu_keyboard())

def main():
    if not hasattr(config, 'BOT_TOKEN'):
        print("❌ خطأ: BOT_TOKEN مفقود!")
        return

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # ربط الأزرار
    app.add_handler(CallbackQueryHandler(games.callback_handler))

    # ربط النصوص
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, global_handler))

    print("🚀 تم التشغيل بنظام المسارات المباشرة...")
    app.run_polling()

if __name__ == '__main__':
    main()
