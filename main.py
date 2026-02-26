import logging
from telegram.ext import Application
from handlers import register_handlers
from config import BOT_TOKEN

# إعداد السجلات (Logs) لمراقبة عمل البوت
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

def main():
    """تشغيل بوت مونوبولي الملكي"""
    try:
        # بناء تطبيق البوت باستخدام التوكن
        app = Application.builder().token(BOT_TOKEN).build()
        
        # استدعاء دالة تسجيل المعالجات من مجلد handlers
        register_handlers(app)

        print("✅ تم تشغيل نظام مونوبولي الملكي بنجاح...")
        
        # تشغيل البوت بنمط Polling (الأكثر استقراراً)
        # drop_pending_updates تضمن تجاهل الرسائل القديمة عند إعادة التشغيل
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ حدث خطأ فادح أثناء التشغيل: {e}")

if __name__ == "__main__":
    main()
