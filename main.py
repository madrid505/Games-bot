import asyncio
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from handlers.bank_handler import bank_logic
from handlers.roulette_handler import roulette_logic
from handlers.interaction_handler import interaction_logic
from handlers.games_handler import handle_messages, callback_handler # ملف الألعاب الأصلي
from config import BOT_TOKEN

async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # الترتيب هنا حيوي جداً لضمان عدم ضياع أي رسالة
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, interaction_logic), group=1)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bank_logic), group=2)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, roulette_logic), group=3)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages), group=4)
    
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("✅ تم تشغيل نظام مونوبولي المطور بنجاح...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(run_bot())
