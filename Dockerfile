# استخدم صورة Python الرسمية
FROM python:3.11-slim

# اضبط متغير العمل داخل الحاوية
WORKDIR /app

# انسخ ملفات المشروع إلى الحاوية
COPY . .

# تثبيت المتطلبات
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# أمر تشغيل البوت
CMD ["python", "main.py"]
