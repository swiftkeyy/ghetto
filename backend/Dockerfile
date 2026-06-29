FROM python:3.12-slim

# Метаданные
LABEL maintainer="GHETTO VPN <dev@ghettovpn.com>"
LABEL description="GHETTO VPN Backend - Premium VPN Service"

# Аргументы сборки
ARG PYTHON_VERSION=3.12
ARG DEBIAN_FRONTEND=noninteractive

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    # WireGuard
    wireguard-tools \
    iptables \
    iproute2 \
    # Утилиты
    net-tools \
    iputils-ping \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p /app/logs /app/configs /app/tmp && \
    chmod -R 755 /app

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 ghettovpn && \
    chown -R ghettovpn:ghettovpn /app

# Переключение на непривилегированного пользователя
USER ghettovpn

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/home/ghettovpn/.local/bin:$PATH"

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose портов
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
