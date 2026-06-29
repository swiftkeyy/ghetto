# 🚂 Деплой GHETTO VPN на Railway

## ✅ Что подходит для Railway:

- ✅ Backend (FastAPI + aiogram bot)
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ Admin Panel (Next.js)

## ⚠️ Ограничения Railway:

- Railway предоставляет 5$ бесплатно в месяц
- Ограничение на количество одновременных сервисов
- VPN серверы нужно размещать отдельно (на VPS)

---

## 🚀 Пошаговый деплой

### Вариант 1: Все сервисы на Railway (рекомендуется для тестирования)

#### 1. Подготовка проекта

Создайте `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn src.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 2. Создайте Procfile для backend:

```
web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
worker: python -m src.bot.main
```

#### 3. Настройка на Railway:

**Шаг 1: Создайте новый проект**
1. Зайдите на [Railway.app](https://railway.app)
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"

**Шаг 2: Добавьте PostgreSQL**
1. В проекте нажмите "+ New"
2. Выберите "Database" → "PostgreSQL"
3. Railway автоматически создаст переменную `DATABASE_URL`

**Шаг 3: Добавьте Redis**
1. Нажмите "+ New"
2. Выберите "Database" → "Redis"
3. Railway создаст `REDIS_URL`

**Шаг 4: Настройте Backend**
1. Нажмите "+ New" → "GitHub Repo"
2. Выберите ваш репозиторий
3. Root Directory: `/backend`
4. Добавьте переменные окружения:

```env
BOT_TOKEN=your_bot_token
SECRET_KEY=your_secret_key_min_32_chars
JWT_SECRET_KEY=your_jwt_secret_min_32_chars
ADMIN_USER_IDS=your_telegram_id

# Railway автоматически предоставит:
# DATABASE_URL
# REDIS_URL
# PORT

# Дополнительные настройки
ENVIRONMENT=production
DEBUG=False

# Webhook (будет доступен после деплоя)
BOT_WEBHOOK_URL=https://your-app.railway.app/webhook
BOT_WEBHOOK_SECRET=generate_random_secret
```

**Шаг 5: Deploy Admin Panel**
1. Создайте еще один сервис "+ New" → "GitHub Repo"
2. Root Directory: `/admin`
3. Build Command: `npm install && npm run build`
4. Start Command: `npm start`
5. Переменные окружения:

```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
NEXTAUTH_URL=https://your-admin.railway.app
NEXTAUTH_SECRET=your_nextauth_secret
```

---

### Вариант 2: Только Backend на Railway (для продакшн)

Если хотите сэкономить ресурсы:

1. **Backend + Bot** на Railway
2. **Admin Panel** на Vercel (бесплатно)
3. **VPN серверы** на отдельных VPS (DigitalOcean, Hetzner и т.д.)

---

## 📝 Модификации для Railway

### 1. Обновите `backend/src/main.py`

Добавьте поддержку переменной окружения `PORT`:

```python
import os

# В конце файла
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
```

### 2. Обновите `backend/requirements.txt`

Добавьте gunicorn для продакшн:

```txt
gunicorn==21.2.0
```

### 3. Создайте `backend/railway.toml`

```toml
[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "on-failure"
```

---

## 🔧 Настройка Webhook для Telegram

После деплоя на Railway:

1. **Получите URL вашего backend**:
   - Зайдите в Settings → Domains
   - Скопируйте URL (например: `your-app.railway.app`)

2. **Установите webhook**:

```bash
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d "url=https://your-app.railway.app/webhook/your_secret" \
  -d "secret_token=your_webhook_secret"
```

3. **Проверьте webhook**:

```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

---

## 💡 Оптимизация для Railway

### 1. Уменьшите размер зависимостей

Создайте `backend/requirements-railway.txt`:

```txt
# Минимальные зависимости для Railway
fastapi==0.109.0
uvicorn[standard]==0.27.0
aiogram==3.4.1
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
redis==5.0.1
python-jose[cryptography]==3.3.0
passlib[argon2]==1.7.4
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

### 2. Используйте Railway Volumes для логов

В `railway.toml`:

```toml
[[volumes]]
mountPath = "/app/logs"
```

---

## 📊 Мониторинг на Railway

Railway предоставляет встроенный мониторинг:

1. **Metrics** - CPU, RAM, Network
2. **Logs** - Все логи в реальном времени
3. **Deployments** - История деплоев

Для расширенного мониторинга используйте внешние сервисы:
- **Sentry** - для ошибок
- **Better Uptime** - для uptime мониторинга

---

## 💰 Стоимость на Railway

### Free Tier (Hobby Plan):
- **$5 кредитов в месяц**
- Достаточно для:
  - Backend (маленький) + PostgreSQL + Redis
  - ~100-500 пользователей

### Pro Plan ($20/месяц):
- Больше ресурсов
- Priority support
- Больше сервисов

### Рекомендация:

Для **тестирования**: Free tier достаточно
Для **продакшн**: Pro plan + отдельные VPN серверы

---

## 🚨 Важные замечания

### 1. VPN Серверы на Railway - НЕ РЕКОМЕНДУЕТСЯ

Railway **не подходит** для размещения VPN серверов, потому что:
- Нет контроля над сетевыми портами (WireGuard нужен UDP)
- Нестабильные IP адреса
- Высокая цена за bandwidth

**Решение**: Размещайте VPN серверы на отдельных VPS:
- DigitalOcean ($4-6/месяц)
- Hetzner ($4-5/месяц)
- Vultr ($3.5-6/месяц)

### 2. Admin Panel на Vercel (бесплатно)

Вместо Railway, деплойте админку на Vercel:

```bash
cd admin
vercel
```

Это сэкономит ресурсы Railway для backend.

---

## 🔐 Безопасность на Railway

1. **Используйте Railway Secrets** для всех чувствительных данных
2. **Не коммитьте .env** в Git
3. **Используйте сильные пароли** для БД
4. **Включите 2FA** для Railway аккаунта

---

## 🐛 Troubleshooting

### Ошибка: "Port already in use"

Railway автоматически присваивает порт через переменную `$PORT`.
Убедитесь, что используете её:

```python
port = int(os.getenv("PORT", 8000))
```

### Ошибка: "Database connection failed"

Railway предоставляет `DATABASE_URL`. Убедитесь, что используете её:

```python
DATABASE_URL = os.getenv("DATABASE_URL")
```

### Bot не отвечает

Проверьте:
1. Webhook установлен правильно
2. `BOT_WEBHOOK_URL` соответствует вашему домену Railway
3. Логи в Railway Dashboard

---

## ✅ Checklist для Railway

- [ ] Создан проект на Railway
- [ ] Добавлен PostgreSQL
- [ ] Добавлен Redis
- [ ] Настроены переменные окружения
- [ ] Backend задеплоен
- [ ] Миграции применены
- [ ] Webhook установлен
- [ ] Бот отвечает на /start
- [ ] Admin panel задеплоен (Railway или Vercel)
- [ ] VPN серверы настроены на отдельных VPS

---

## 🎯 Рекомендуемая архитектура для продакшн

```
Railway:
├── Backend API + Bot (1 service)
├── PostgreSQL (managed)
└── Redis (managed)

Vercel:
└── Admin Panel (бесплатно)

VPS (DigitalOcean/Hetzner):
├── VPN Server 1 (WireGuard)
├── VPN Server 2 (VLESS)
└── VPN Server 3 (...)
```

**Стоимость**: ~$25-30/месяц для начала

---

## 📞 Дополнительная помощь

Если нужна помощь с деплоем:

1. Railway Docs: https://docs.railway.app
2. Railway Discord: https://discord.gg/railway
3. Vercel Docs: https://vercel.com/docs

---

**Railway подходит для Backend + Database + Admin Panel**  
**VPN серверы нужно размещать отдельно на VPS!** ⚠️
