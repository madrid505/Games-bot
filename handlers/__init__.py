from .games_handler import handle_messages, callback_handler

# هذا الملف يعمل كجسر لربط ملف الألعاب والبنك والفعاليات
# بحيث يقرأ ملف main.py الوظائف الأساسية مباشرة

__all__ = ['handle_messages', 'callback_handler']
