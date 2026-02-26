from telegram import Update
from telegram.ext import ContextTypes
from config import OWNER_ID

async def is_owner_or_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    member = await chat.get_member(user.id)
    return user.id == OWNER_ID or member.status in ['administrator', 'creator']
