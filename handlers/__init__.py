from telegram.ext import MessageHandler, CallbackQueryHandler, filters
from .games_handler import handle_messages, callback_handler

def register_handlers(app):
    # إضافة معالج الرسائل النصية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    # إضافة معالج الأزرار (القائمة)
    app.add_handler(CallbackQueryHandler(callback_handler))
