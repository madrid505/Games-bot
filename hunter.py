from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from config import OWNER_ID

async def catch_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # لا يستجيب إلا للمالك وفي الخاص فقط
    if update.effective_user.id == OWNER_ID:
        if update.message.photo:
            p_id = update.message.photo[-1].file_id
            await update.message.reply_html(f"<code>{p_id}=الجواب_هنا</code>")

# هذا الهاندلر يتم استدعاؤه في الملف الأساسي
hunter_handler = MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, catch_photo)
