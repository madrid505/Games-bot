import logging
from telegram.ext import Application
from handlers import register_handlers
from config import BOT_TOKEN

# إعداد السجلات لمراقبة الأداء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

def main():
    """تشغيل البوت بنظام الملفات المنفصلة"""
    try:
        # إنشاء التطبيق
        app = Application.builder().token(BOT_TOKEN).build()
        
        # تسجيل جميع المعالجات (البنك، الروليت، التفاعل، الألعاب)
        register_handlers(app)

        print("✅ تم تشغيل نظام ميسك الملكي بنجاح...")
        
        # تشغيل البوت بالطريقة المباشرة والمتوافقة مع السيرفر
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ حدث خطأ أثناء تشغيل البوت: {e}")

if __name__ == "__main__":
    main()
