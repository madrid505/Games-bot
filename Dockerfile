# Dockerfile games-bot
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir telethon Pillow

RUN mkdir -p /app/data && chmod 777 /app/data

CMD ["python", "games_main.py"]  # غير اسم الملف الرئيسي إذا مختلف
