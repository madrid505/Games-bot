from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, CallbackQueryHandler, filters
import random
import json
from core.security import check_allowed_group
from database.db import init_db

class QuizGame:
    QUESTIONS_FILES = [
        'games/data/questions_general.json',
        'games/data/questions_islamic.json',
        'games/data/questions_flags.json'
    ]

    @staticmethod
    async def register_handlers(app):
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, QuizGame.handle_message))
        app.add_handler(CallbackQueryHandler(QuizGame.callback_handler))

    @staticmethod
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if not check_allowed_group(chat_id):
            return
        text = update.message.text.strip()
        # لاحقاً ربط اسم اللعبة بالكتابة لتشغيلها

    @staticmethod
    async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        # لاحقاً التعامل مع الضغط على زر اللعبة
