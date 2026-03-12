# 👑 نظام الوصل الملكي - إمبراطورية مونوبولي 2026 👑
# هذا الملف ينظم استيراد جميع المعالجات لضمان عمل البوت بسلاسة

from .games_handler import handle_messages, callback_handler
from .bank_handler import handle_bank

# تصدير الدوال الأساسية لتكون متاحة عند استدعاء مجلد handlers
__all__ = [
    'handle_messages', 
    'callback_handler', 
    'handle_bank'
]

# ملاحظة: تم التأكد من ربط نظام الألبومات والبنك ضمن قائمة التصدير
