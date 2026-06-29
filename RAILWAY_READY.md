# 🎉 GHETTO VPN - Готов к деплою на Railway!

## ✅ Что было добавлено для Railway

### Новые файлы:
1. ✅ `backend/railway.json` - конфигурация Railway
2. ✅ `backend/Procfile` - команды запуска
3. ✅ `backend/nixpacks.toml` - настройки сборки
4. ✅ `RAILWAY_DEPLOY.md` - полная инструкция по деплою
5. ✅ Обновлен `backend/src/main.py` - поддержка $PORT

---

## 🚀 Быстрый деплой на Railway (3 шага)

### Шаг 1: Создайте проект на Railway

1. Зайдите на [railway.app](https://railway.app)
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Подключите репозиторий

### Шаг 2: Добавьте сервисы

**PostgreSQL:**
- Нажмите "+ New" → "Database" → "PostgreSQL"
- Railway автоматически создаст `DATABASE_URL`

**Redis:**
- Нажмите "+ New" → "Database" → "Redis"
- Railway автоматически создаст `REDIS_URL`

### Шаг 3: Настройте переменные окружения

В настройках Backend добавьте:

```env
# ОБЯЗАТЕЛЬНЫЕ
BOT_TOKEN=ваш_токен_от_botfather
SECRET_KEY=минимум_32_символа_случайная_строка
JWT_SECRET_KEY=минимум_32_символа_случайная_строка
ADMIN_USER_IDS=ваш_telegram_id

# WEBHOOK (после первого деплоя)
BOT_WEBHOOK_URL=https://ваш-домен.railway.app/webhook
BOT_WEBHOOK_SECRET=случайная_строка_для_безопасности

# ОПЦИОНАЛЬНЫЕ (Railway предоставит автоматически)
# DATABASE_URL - автоматически от PostgreSQL
# REDIS_URL - автоматически от Redis
# PORT - автоматически от Railway
```

**Готово!** Railway автоматически задеплоит проект.

---

## 📊 Архитектура на Railway

### Рекомендуемая конфигурация:

```
Railway Project:
├── Backend Service
│   ├── FastAPI + aiogram bot
│   └── Root Directory: /backend
├── PostgreSQL (managed)
└── Redis (managed)

Отдельно:
├── Admin Panel → Vercel (бесплатно)
└── VPN Servers → VPS (DigitalOcean, Hetzner)
```

---

## 💰 Стоимость

### Hobby Plan (Free):
- **$5 кредитов/месяц**
- Хватит на:
  - Backend (small)
  - PostgreSQL
  - Redis
  - ~500-1000 пользователей

### Pro Plan ($20/месяц):
- Больше ресурсов
- Приоритетная поддержка
- Для серьезных проектов

---

## ⚙️ Настройка Webhook

После первого деплоя:

1. **Получите ваш Railway URL:**
   - Settings → Domains
   - Скопируйте: `your-app-name.up.railway.app`

2. **Установите webhook:**

```bash
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d "url=https://your-app-name.up.railway.app/webhook/your_secret" \
  -d "secret_token=your_webhook_secret"
```

3. **Обновите переменные в Railway:**
   - `BOT_WEBHOOK_URL=https://your-app-name.up.railway.app/webhook`
   - `BOT_WEBHOOK_SECRET=ваш_секретный_токен`

4. **Перезапустите сервис**

---

## ⚠️ Важные замечания

### ✅ Подходит для Railway:
- Backend API
- Telegram Bot (через webhook)
- PostgreSQL database
- Redis cache
- Admin Panel (но лучше на Vercel)

### ❌ НЕ подходит для Railway:
- **VPN серверы** - нужны отдельные VPS!
  - Railway не поддерживает UDP порты (нужны для WireGuard)
  - Нет статических IP адресов
  - Высокая стоимость bandwidth

### 🎯 Решение:
Используйте Railway для backend + bot, а VPN серверы размещайте на:
- **DigitalOcean** ($4-6/месяц за VPS)
- **Hetzner** ($4-5/месяц за VPS)
- **Vultr** ($3.5-6/месяц за VPS)

---

## 🔧 Проверка работы

### 1. Проверьте health endpoint:

```bash
curl https://your-app-name.up.railway.app/health
```

Должен вернуть:
```json
{
  "status": "healthy",
  "redis": "connected",
  "environment": "production"
}
```

### 2. Проверьте webhook:

```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

### 3. Протестируйте бота:
- Найдите вашего бота в Telegram
- Отправьте `/start`
- Должно появиться приветственное сообщение

---

## 📝 Чеклист деплоя

- [ ] Репозиторий создан на GitHub
- [ ] Проект создан на Railway
- [ ] PostgreSQL добавлен
- [ ] Redis добавлен
- [ ] Переменные окружения настроены
- [ ] Backend задеплоен успешно
- [ ] Логи проверены (нет ошибок)
- [ ] Health endpoint отвечает
- [ ] Webhook установлен
- [ ] Бот отвечает на /start
- [ ] Миграции применены автоматически
- [ ] VPN серверы настроены на VPS
- [ ] Серверы добавлены в админке

---

## 🐛 Troubleshooting

### Ошибка: "Application failed to respond"

**Причина:** Приложение не успевает запуститься за 100 секунд.

**Решение:**
1. Увеличьте `healthcheckTimeout` в `railway.json`
2. Проверьте логи в Railway Dashboard
3. Убедитесь, что миграции выполняются быстро

### Ошибка: "Database connection failed"

**Решение:**
1. Проверьте, что PostgreSQL сервис запущен
2. Railway должен автоматически создать `DATABASE_URL`
3. Проверьте в Variables → `DATABASE_URL` существует

### Бот не отвечает

**Решение:**
1. Проверьте webhook: `getWebhookInfo`
2. Убедитесь, что `BOT_WEBHOOK_URL` правильный
3. Проверьте логи в Railway
4. Убедитесь, что `BOT_WEBHOOK_SECRET` совпадает

---

## 🎯 Следующие шаги

После успешного деплоя на Railway:

1. **Настройте VPN серверы** на отдельных VPS
2. **Добавьте серверы** через админ-панель
3. **Задеплойте Admin Panel** на Vercel (бесплатно)
4. **Настройте домен** (опционально)
5. **Настройте мониторинг** (Better Uptime, Sentry)
6. **Протестируйте** все функции
7. **Запускайте!** 🚀

---

## 📚 Документация

Читайте подробные инструкции:

1. **RAILWAY_DEPLOY.md** - Полный гайд по Railway
2. **INSTALLATION.md** - Общая установка
3. **QUICKSTART.md** - Быстрый старт
4. **PROJECT_SUMMARY.md** - Обзор проекта

---

## 💡 Оптимальная конфигурация для старта

```
Backend + Bot:     Railway ($5-20/месяц)
Admin Panel:       Vercel (бесплатно)
VPN Server 1:      DigitalOcean ($5/месяц)
VPN Server 2:      Hetzner ($4/месяц)
Domain:            Cloudflare (бесплатно)
Monitoring:        Better Uptime (бесплатно)

Итого: ~$15-30/месяц
```

---

## ✅ Финальный статус

**Проект GHETTO VPN полностью готов к деплою на Railway!**

Все необходимые файлы созданы:
- ✅ railway.json
- ✅ Procfile
- ✅ nixpacks.toml
- ✅ main.py обновлен
- ✅ Документация готова

**Можно деплоить прямо сейчас!** 🚀

---

Создано: 29.06.2026  
Версия: 1.0.0  
Railway Ready: ✅
