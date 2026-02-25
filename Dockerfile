# استخدام نسخة خفيفة من بايثون
FROM python:3.10-slim

# تحديد مجلد العمل داخل السيرفر
WORKDIR /app

# نسخ الملفات من GitHub إلى السيرفر
COPY . .

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir -r requirements.txt

# أمر تشغيل البوت
CMD ["python", "main.py"]
