# ⚡ GHETTO VPN - Быстрый старт за 5 минут

## 🚀 Минимальная настройка для тестирования

### Шаг 1: Получение токена бота (2 минуты)

1. Откройте Telegram и найдите [@BotFather](https://t.me/botfather)
2. Отправьте команду `/newbot`
3. Введите название: `My VPN Bot`
4. Введите username: `my_vpn_test_bot` (должен заканчиваться на `_bot`)
5. **Скопируйте токен** (выглядит как `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Шаг 2: Настройка проекта (1 минута)

```bash
# Перейдите в папку проекта
cd "Ghetto vpn"

# Скопируйте файл окружения
copy .env.example .env

# Откройте .env в блокноте
notepad .env
```

Измените только эти строки:
```env
BOT_TOKEN=ваш_токен_от_botfather
POSTGRES_PASSWORD=qwerty123
SECRET_KEY=my_super_secret_key_12345678901234567890
JWT_SECRET_KEY=jwt_secret_12345678901234567890123456
```

Сохраните и закройте файл.

### Шаг 3: Запуск (2 минуты)

```bash
# Запустите все сервисы
docker-compose up -d

# Дождитесь запуска (30-60 секунд)
# Проверьте статус
docker-compose ps
```

Все сервисы должны быть в статусе `Up`.

### Шаг 4: Применение миграций

```bash
# Создание таблиц в базе данных
docker-compose exec backend alembic upgrade head
```

### Шаг 5: Тестирование бота

1. Найдите вашего бота в Telegram
2. Нажмите **Start** или отправьте `/start`
3. Вы должны увидеть приветственное сообщение с inline кнопками

**Готово!** Бот работает! 🎉

---

## 🔧 Доступ к сервисам

После запуска доступны:

| Сервис | URL | Описание |
|--------|-----|----------|
| **Telegram Bot** | Ваш бот в Telegram | Основной интерфейс |
| **API Docs** | http://localhost:8000/docs | Swagger документация |
| **Admin Panel** | http://localhost:3000 | Админ панель |
| **Grafana** | http://localhost:3001 | Мониторинг |
| **Prometheus** | http://localhost:9090 | Метрики |

---

## 👤 Создание администратора

Чтобы получить доступ к админке:

1. **Получите свой Telegram ID**:
   - Откройте [@userinfobot](https://t.me/userinfobot)
   - Отправьте любое сообщение
   - Скопируйте ваш ID (например: `123456789`)

2. **Добавьте ID в .env**:
   ```env
   ADMIN_USER_IDS=123456789
   ```

3. **Перезапустите backend**:
   ```bash
   docker-compose restart backend
   ```

4. **Отправьте `/start` боту** - теперь вы администратор!

---

## 📱 Тестирование функций

### Основные функции бота:

```
/start           - Главное меню
Серверы          - Список VPN серверов
Устройства       - Добавление устройств
Подписки         - Тарифные планы
Профиль          - Информация о вас
Рефералы         - Реферальная программа
```

### Тестовый flow:

1. **Регистрация**: Нажмите "Начать" в приветствии
2. **Trial**: Активируйте 3 дня бесплатно
3. **Устройство**: Добавьте Android устройство
4. **Конфиг**: Получите QR-код для подключения

---

## 🛠️ Полезные команды

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только backend (бот)
docker-compose logs -f backend

# Только админка
docker-compose logs -f admin

# Последние 100 строк
docker-compose logs --tail=100 backend
```

### Перезапуск сервисов

```bash
# Все сервисы
docker-compose restart

# Только backend
docker-compose restart backend

# Только admin
docker-compose restart admin
```

### Остановка и удаление

```bash
# Остановить все сервисы
docker-compose stop

# Остановить и удалить контейнеры
docker-compose down

# Удалить с volumes (БД будет очищена!)
docker-compose down -v
```

---

## 🐛 Решение проблем

### Бот не отвечает

```bash
# Проверьте логи
docker-compose logs backend | findstr "ERROR"

# Проверьте токен
echo %BOT_TOKEN%

# Перезапустите
docker-compose restart backend
```

### База данных не работает

```bash
# Проверьте статус
docker-compose ps postgres

# Пересоздайте
docker-compose down -v
docker-compose up -d postgres
timeout /t 10
docker-compose exec backend alembic upgrade head
```

### Порты заняты

Если порт 8000, 3000 или 5432 занят:

```bash
# Измените порты в docker-compose.yml
# Например, для backend:
ports:
  - "8001:8000"  # Вместо 8000:8000
```

---

## 📊 Проверка работоспособности

### 1. Backend API

Откройте браузер: http://localhost:8000/health

Должно быть:
```json
{
  "status": "healthy",
  "redis": "connected",
  "environment": "production"
}
```

### 2. Admin Panel

Откройте: http://localhost:3000

Должна открыться страница с логотипом GHETTO VPN.

### 3. Database

```bash
docker-compose exec postgres psql -U ghettovpn -d ghettovpn -c "SELECT COUNT(*) FROM users;"
```

Если команда выполняется без ошибок - БД работает.

---

## 🎯 Следующие шаги

После того как все заработало:

1. **Прочитайте** `INSTALLATION.md` для детальной настройки
2. **Настройте VPN серверы** (WireGuard или VLESS)
3. **Добавьте серверы** через админ-панель
4. **Настройте платежи** (Stripe, Crypto, ЮKassa)
5. **Протестируйте** все функции
6. **Разверните** на реальный сервер для продакшн

---

## 💡 Советы

### Разработка

- Используйте `docker-compose logs -f backend` для отладки
- API документация доступна на `/docs`
- Меняйте код в `backend/src/` - изменения применятся автоматически (hot reload)

### Тестирование

- Создайте несколько тестовых аккаунтов в Telegram
- Протестируйте все flow пользователя
- Проверьте работу на разных устройствах

### Продакшн

- Обязательно измените все пароли и секретные ключи
- Настройте SSL сертификаты (Let's Encrypt)
- Включите бэкапы базы данных
- Настройте мониторинг и алерты

---

## 📞 Помощь

Если что-то не работает:

1. **Проверьте логи**: `docker-compose logs -f`
2. **Проверьте .env**: все ли заполнено правильно?
3. **Проверьте Docker**: `docker ps`, все ли контейнеры запущены?
4. **Перезапустите**: `docker-compose restart`
5. **Пересоздайте**: `docker-compose down && docker-compose up -d`

---

## ✅ Готово!

Если вы дошли до этого момента и всё работает - **поздравляем!** 🎉

У вас теперь есть полноценный VPN сервис уровня Telegram Premium.

**Следующий шаг**: Прочитайте `INSTALLATION.md` для настройки продакшн версии.

---

**Время настройки**: 5 минут ⚡  
**Сложность**: Легко 🟢  
**Результат**: Работающий VPN бот 🚀
