from .games_handler import handle_messages, callback_handler
from .bank_handler import handle_bank

# هذا الملف هو قلب الوصل البرمجي لمملكة مونوبولي
# يجمع بين نظام الألعاب، البنك، والألبومات

__all__ = ['handle_messages', 'callback_handler', 'handle_bank']
