import logging
import random
import asyncio
import os
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, PicklePersistence 
from config import BOT_TOKEN, OWNER_ID, GROUP_IDS
from handlers.games_handler import handle_messages, callback_handler
from telegram import Update
from telegram.ext import ContextTypes
from royal_messages import GUESS_START_ANNOUNCEMENT

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u_id = update.effective_user.id
    if update.effective_chat.type == 'private':
        if context.args and context.args[0].startswith("guess_"):
            parts = context.args[0].split("_")
            target_chat_id = parts[1]
            allowed_admin_id = int(parts[2]) if len(parts) > 2 else None
            if allowed_admin_id and u_id != allowed_admin_id:
                await update.message.reply_text("⚠️ **عفواً:** هذا الزر مخصص للمشرف الذي أطلقه فقط!")
                return
            context.user_data['awaiting_guess_for'] = target_chat_id
            await update.message.reply_text("🎯 أهلاً بك يا سيادة المشرف... أرسل الرقم السري:")
            return
        await update.message.reply_text("👑 أهلاً بك في بوت إمبراطورية مونوبولي.")

async def image_hunter_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """صياد الصور: يعمل فقط في الخاص ومع المالك فقط"""
    if update.message.photo and update.effective_chat.type == 'private' and update.effective_user.id == OWNER_ID:
        file_id = update.message.photo[-1].file_id
        text = (
            "🎯 **تم اصطياد المعرف الملكي للصورة!**\n\n"
            f"`{file_id}`\n\n"
            "✨ *استخدم هذا المعرف في ملفات الألعاب الخاصة بك.*"
        )
        await update.message.reply_text(text, parse_mode='Markdown')

async def catch_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    u_id = update.effective_user.id
    text = update.message.text.strip() if update.message.text else ""

    if update.effective_chat.type == 'private':
        target_chat_id = context.user_data.get('awaiting_guess_for')
        if target_chat_id and text and text.isdigit():
            context.bot_data[f"guess_ans_{target_chat_id}"] = text
            # (تكملة منطق التخمين والعد التنازلي كما هي في كودك...)
            # ...
            return

    if update.effective_chat.id in [int(i) for i in GROUP_IDS] or u_id == OWNER_ID:
        if update.message.text or update.message.photo:
            await handle_messages(update, context)

def main():
    volume_path = "/app/data"
    games_dir = os.path.join(volume_path, "games_data")
    if not os.path.exists(games_dir): os.makedirs(games_dir)
    
    persistence = PicklePersistence(filepath=os.path.join(games_dir, "games_persistence"))
    app = ApplicationBuilder().token(BOT_TOKEN).persistence(persistence).build()

    # الترتيب هنا هو سر النجاح:
    app.add_handler(CommandHandler("start", start))
    
    # 1. نضع الصياد أولاً ليفحص الصور في الخاص
    app.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, image_hunter_private))
    
    # 2. ثم نضع المعالج العام لكل الرسائل الأخرى
    app.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), catch_ids))
    
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    print("👑 إمبراطورية مونوبولي تعمل الآن...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
