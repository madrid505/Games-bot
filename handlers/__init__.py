from telegram.ext import MessageHandler, CallbackQueryHandler, filters
from .games_handler import handle_messages, callback_handler
from .bank_handler import bank_logic
from .roulette_handler import roulette_logic
from .interaction_handler import interaction_logic

def register_handlers(app):
    # استخدام المجموعات (group) يضمن أن كل ملف يستلم الرسالة ويعالجها بشكل مستقل
    
    # المجموعة 1: ملك التفاعل (يجب أن يكون أولاً ليحسب كل رسالة)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, interaction_logic), group=1)
    
    # المجموعة 2: أوامر البنك (رصيدي، راتب، زرف...)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bank_logic), group=2)
    
    # المجموعة 3: الروليت (انا، تم، روليت)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, roulette_logic), group=3)
    
    # المجموعة 4: الألعاب (تشغيل الألعاب والتحقق من الإجابات)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages), group=4)
    
    # أزرار القائمة
    app.add_handler(CallbackQueryHandler(callback_handler))
