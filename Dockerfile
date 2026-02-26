# استخدم صورة Python الرسمية
FROM python:3.11-slim

# تحديد مجلد العمل داخل الحاوية
WORKDIR /app

# نسخ كل ملفات المشروع إلى الحاوية
COPY . .

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# ضبط المتغيرات البيئية
ENV PYTHONUNBUFFERED=1

# بدء البوت تلقائياً
CMD ["python", "main.py"]
