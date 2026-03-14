# ملف: Dockerfile
FROM python:3.9-slim

# تثبيت مكتبات النظام اللازمة لمعالجة الصور
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ كل الملفات
COPY . .

# تثبيت المكتبات البرمجية المطلوبة للبوت
RUN pip install --no-cache-dir python-telegram-bot==20.5 Pillow

# أمر التشغيل
CMD ["python3", "main.py"]
