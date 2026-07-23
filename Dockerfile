FROM python:3.12-slim

# Muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

# Tizim paketlari
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python paketlari
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Loyiha fayllari
COPY . .

# entrypoint skript — migratsiya + statik fayllar + gunicorn
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]