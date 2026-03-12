import json
import os
import logging

# إعداد السجلات لمراقبة الأخطاء في تحميل الأسئلة
logger = logging.getLogger(__name__)

def load_questions():
    # المسار لمجلد data داخل مجلد games
    folder = os.path.join(os.path.dirname(__file__), 'data')
    questions = {}
    
    # التأكد من وجود المجلد أولاً لتجنب توقف البوت
    if not os.path.exists(folder):
        logger.error(f"⚠️ تحذير ملكي: مجلد الأسئلة غير موجود في {folder}")
        return questions

    for file in os.listdir(folder):
        if file.endswith('.json'):
            # استخراج اسم اللعبة من اسم الملف (مثال: questions_islamic.json -> islamic)
            key = file.replace('questions_', '').replace('.json', '')
            file_path = os.path.join(folder, file)
            
            try:
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        questions[key] = data
                    else:
                        logger.warning(f"⚠️ ملف {file} ليس بتنسيق قائمة (List).")
            except Exception as e:
                logger.error(f"❌ خطأ في تحميل ملف الأسئلة {file}: {e}")
                
    return questions
