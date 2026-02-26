from .games_handler import handle_messages, callback_handler
def register_handlers(app):
    from telegram.ext import MessageHandler, CallbackQueryHandler, filters
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    app.add_handler(CallbackQueryHandler(callback_handler))
