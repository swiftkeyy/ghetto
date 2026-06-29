# 🚀 GHETTO VPN - Руководство по установке и запуску

## 📋 Содержание

1. [Требования](#требования)
2. [Быстрый старт](#быстрый-старт)
3. [Настройка Backend](#настройка-backend)
4. [Настройка Admin Panel](#настройка-admin-panel)
5. [Настройка базы данных](#настройка-базы-данных)
6. [Настройка Telegram бота](#настройка-telegram-бота)
7. [Настройка VPN серверов](#настройка-vpn-серверов)
8. [Развертывание в продакшн](#развертывание-в-продакшн)
9. [Troubleshooting](#troubleshooting)

---

## 🔧 Требования

### Минимальные требования:
- **OS**: Ubuntu 20.04+ / Debian 11+ / Windows 10+ (для разработки)
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 20 GB SSD
- **Python**: 3.12+
- **Node.js**: 20+
- **Docker**: 24+
- **PostgreSQL**: 16+
- **Redis**: 7+

---

## ⚡ Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/ghetto-vpn.git
cd ghetto-vpn
```

### 2. Настройка переменных окружения

```bash
cp .env.example .env
```

Откройте `.env` и заполните основные параметры:

```env
# Telegram Bot
BOT_TOKEN=your_bot_token_from_botfather

# Database
POSTGRES_PASSWORD=your_secure_password

# Security
SECRET_KEY=your_secret_key_generate_random
JWT_SECRET_KEY=your_jwt_secret_key
```

### 3. Запуск с Docker Compose

```bash
docker-compose up -d
```

### 4. Применение миграций

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Создание администратора

```bash
docker-compose exec backend python -m src.cli create-admin
```

### 6. Проверка статуса

```bash
docker-compose ps
```

Все сервисы должны быть в состоянии `Up`.

---

## 🐍 Настройка Backend

### Локальная разработка (без Docker)

#### 1. Создание виртуального окружения

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

#### 3. Запуск PostgreSQL и Redis

```bash
# PostgreSQL
docker run -d --name ghettovpn_postgres \
  -e POSTGRES_DB=ghettovpn \
  -e POSTGRES_USER=ghettovpn \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:16-alpine

# Redis
docker run -d --name ghettovpn_redis \
  -p 6379:6379 \
  redis:7-alpine
```

#### 4. Применение миграций

```bash
alembic upgrade head
```

#### 5. Запуск бота

```bash
python -m src.bot.main
```

#### 6. Запуск API (в отдельном терминале)

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🎨 Настройка Admin Panel

### Локальная разработка

#### 1. Установка зависимостей

```bash
cd admin
npm install
```

#### 2. Настройка переменных

Создайте файл `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret
```

#### 3. Запуск dev-сервера

```bash
npm run dev
```

Админ-панель будет доступна по адресу: `http://localhost:3000`

#### 4. Сборка для продакшн

```bash
npm run build
npm run start
```

---

## 🗄️ Настройка базы данных

### Создание миграции

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Применение миграций

```bash
alembic upgrade head
```

### Откат миграции

```bash
alembic downgrade -1
```

### Просмотр истории

```bash
alembic history
```

---

## 🤖 Настройка Telegram бота

### 1. Создание бота через @BotFather

1. Откройте Telegram и найдите [@BotFather](https://t.me/botfather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 2. Настройка команд бота

Отправьте @BotFather команду `/setcommands` и выберите ваш бот.

Вставьте следующие команды:

```
start - Начать работу с ботом
help - Помощь
profile - Мой профиль
subscriptions - Подписки
servers - Список серверов
devices - Мои устройства
support - Поддержка
```

### 3. Настройка веб-хука (для продакшн)

```bash
# Установка webhook
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d "url=https://yourdomain.com/webhook/your_secret" \
  -d "secret_token=your_webhook_secret"

# Проверка webhook
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

### 4. Получение своего Telegram ID (для админа)

Отправьте любое сообщение боту [@userinfobot](https://t.me/userinfobot) и скопируйте ваш ID.

Добавьте его в `.env`:

```env
ADMIN_USER_IDS=123456789,987654321
```

---

## 🌐 Настройка VPN серверов

### WireGuard

#### Установка на сервер

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install wireguard

# Генерация ключей
wg genkey | tee privatekey | wg pubkey > publickey
```

#### Настройка конфигурации

```bash
sudo nano /etc/wireguard/wg0.conf
```

```ini
[Interface]
PrivateKey = SERVER_PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
# Peers will be added dynamically by the system
```

#### Запуск WireGuard

```bash
sudo systemctl enable wg-quick@wg0
sudo systemctl start wg-quick@wg0
```

### Xray (VLESS Reality)

#### Установка Xray

```bash
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
```

#### Настройка конфигурации

```bash
sudo nano /usr/local/etc/xray/config.json
```

Пример конфигурации VLESS Reality в `/etc/xray/config.json`

#### Запуск Xray

```bash
sudo systemctl enable xray
sudo systemctl start xray
```

---

## 🚀 Развертывание в продакшн

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install docker-compose-plugin
```

### 2. Настройка домена

Добавьте A-записи в DNS:

```
api.yourdomain.com -> YOUR_SERVER_IP
admin.yourdomain.com -> YOUR_SERVER_IP
```

### 3. Настройка SSL (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификатов
sudo certbot --nginx -d api.yourdomain.com -d admin.yourdomain.com
```

### 4. Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/ghettovpn
```

Пример конфигурации в `nginx/conf.d/default.conf`

### 5. Запуск в продакшн

```bash
docker-compose -f docker-compose.yml up -d
```

### 6. Настройка мониторинга

Доступ к Grafana: `http://your-server-ip:3001`

Логин по умолчанию:
- Username: `admin`
- Password: `admin` (измените при первом входе)

---

## 📊 Мониторинг и логи

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f admin
```

### Prometheus метрики

Доступны по адресу: `http://your-server-ip:9090`

### Grafana дашборды

Доступны по адресу: `http://your-server-ip:3001`

---

## 🔍 Troubleshooting

### Бот не отвечает

```bash
# Проверка логов
docker-compose logs backend

# Проверка webhook
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo

# Перезапуск бота
docker-compose restart backend
```

### Ошибки базы данных

```bash
# Проверка подключения
docker-compose exec postgres psql -U ghettovpn -d ghettovpn

# Пересоздание базы (ВНИМАНИЕ: удалит все данные)
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Проблемы с VPN подключением

```bash
# Проверка статуса WireGuard
sudo wg show

# Проверка логов Xray
sudo journalctl -u xray -f

# Проверка портов
sudo netstat -tulpn | grep 51820
```

### Админ-панель не загружается

```bash
# Проверка логов
docker-compose logs admin

# Пересборка
cd admin
npm run build
docker-compose up -d --build admin
```

---

## 📝 Дополнительные команды

### Бэкап базы данных

```bash
docker-compose exec postgres pg_dump -U ghettovpn ghettovpn > backup.sql
```

### Восстановление из бэкапа

```bash
docker-compose exec -T postgres psql -U ghettovpn ghettovpn < backup.sql
```

### Очистка Docker

```bash
docker system prune -a --volumes
```

---

## 🔐 Безопасность

1. **Измените все дефолтные пароли** в `.env`
2. **Используйте сильные секретные ключи** (минимум 32 символа)
3. **Настройте firewall**:
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 51820/udp
   sudo ufw enable
   ```
4. **Регулярно обновляйте систему**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
5. **Настройте автоматические бэкапы**

---

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи: `docker-compose logs -f`
2. Проверьте документацию: `docs/`
3. Создайте issue на GitHub
4. Напишите в поддержку: support@ghettovpn.com

---

## 📄 Лицензия

Proprietary - All Rights Reserved

---

**Создано с ❤️ для GHETTO VPN**
