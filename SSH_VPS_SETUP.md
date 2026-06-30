# 🔐 SSH Настройка VPS для автоматического управления ключами

## 📋 Обзор

GHETTO VPN теперь поддерживает **автоматическое создание и удаление VPN ключей** прямо на VPS через SSH. Это означает, что бот сам будет подключаться к вашим серверам и создавать конфигурации для пользователей.

---

## ✅ Преимущества

- ✅ **Автоматизация** - бот сам создаёт ключи на сервере
- ✅ **Безопасность** - ключи создаются напрямую на VPS
- ✅ **Масштабируемость** - легко добавлять новые серверы
- ✅ **Мониторинг** - автоматическая проверка статуса серверов
- ✅ **Синхронизация** - удаление неактивных пользователей

---

## 🚀 Быстрая настройка

### Шаг 1: Подготовка VPS сервера

Подключитесь к вашему VPS:

```bash
ssh root@your-vps-ip
```

### Шаг 2: Установка WireGuard (для WireGuard протокола)

```bash
# Ubuntu/Debian
apt update
apt install -y wireguard wireguard-tools

# Генерация серверных ключей
cd /etc/wireguard
wg genkey | tee server_private.key | wg pubkey > server_public.key
chmod 600 server_private.key

# Создание базового конфига
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
PrivateKey = $(cat server_private.key)
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
EOF

# Включение IP forwarding
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Запуск WireGuard
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0
```

### Шаг 3: Установка Xray (для VLESS протокола)

```bash
# Установка Xray
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install

# Генерация UUID для демо
xray uuid

# Генерация ключей Reality
xray x25519

# Создание базового конфига
cat > /usr/local/etc/xray/config.json << 'EOF'
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "dest": "www.google.com:443",
          "serverNames": ["www.google.com"],
          "privateKey": "YOUR_PRIVATE_KEY",
          "shortIds": [""]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "tag": "direct"
    }
  ]
}
EOF

# Запуск Xray
systemctl enable xray
systemctl start xray
```

### Шаг 4: Настройка SSH доступа

#### Вариант A: По SSH ключу (рекомендуется)

```bash
# На вашем компьютере (не на VPS!)
ssh-keygen -t ed25519 -C "ghettovpn-bot" -f ~/.ssh/ghettovpn_bot

# Скопировать публичный ключ на VPS
ssh-copy-id -i ~/.ssh/ghettovpn_bot.pub root@your-vps-ip

# Получить приватный ключ (сохраните его для настройки бота)
cat ~/.ssh/ghettovpn_bot
```

#### Вариант B: По паролю (менее безопасно)

Просто используйте существующий пароль root.

---

## ⚙️ Настройка сервера в боте

### Через админ-панель в боте:

1. Откройте бота
2. Нажмите **⚡ Админ-панель**
3. Выберите **🌍 Серверы**
4. Нажмите **➕ Добавить сервер**

### Заполните данные:

```
Название: US-NY-1
Страна: United States
Город: New York
IP адрес: 1.2.3.4
Порт: 51820 (для WireGuard) или 443 (для VLESS)
Протокол: WireGuard или VLESS

SSH настройки:
✅ SSH включен: Да
SSH порт: 22
SSH пользователь: root
SSH метод: Ключ (или Пароль)

Если ключ:
  - Вставьте приватный ключ из ~/.ssh/ghettovpn_bot

Если пароль:
  - Введите пароль root

Дополнительно для VLESS:
  - Public Key: (из xray x25519)
  - Short ID: (опционально)
  - SNI: www.google.com
```

---

## 📊 Как это работает

### Создание конфига для пользователя:

1. Пользователь выбирает сервер и нажимает "Подключиться"
2. Бот подключается к VPS через SSH
3. Бот выполняет команды на VPS:
   - Для WireGuard: генерирует ключи, добавляет peer в wg0.conf
   - Для VLESS: генерирует UUID, добавляет клиента в config.json
4. Бот получает конфигурацию и отправляет пользователю QR-код
5. Пользователь импортирует и подключается

### Удаление конфига:

1. Пользователь удаляет устройство или истекает подписка
2. Бот автоматически подключается к VPS
3. Удаляет peer/клиента из конфигурации
4. Перезагружает сервис (wg syncconf или systemctl restart xray)

---

## 🔒 Безопасность

### Рекомендации:

1. **Используйте SSH ключи** вместо паролей
2. **Ограничьте SSH доступ** только для бота:

```bash
# Создать отдельного пользователя для бота
useradd -m -s /bin/bash ghettovpn-bot

# Добавить в sudoers для управления WireGuard/Xray
echo "ghettovpn-bot ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/systemctl" >> /etc/sudoers

# Настроить SSH ключ для этого пользователя
mkdir -p /home/ghettovpn-bot/.ssh
cat > /home/ghettovpn-bot/.ssh/authorized_keys << EOF
ssh-ed25519 AAAA... ghettovpn-bot
EOF
chmod 700 /home/ghettovpn-bot/.ssh
chmod 600 /home/ghettovpn-bot/.ssh/authorized_keys
chown -R ghettovpn-bot:ghettovpn-bot /home/ghettovpn-bot/.ssh
```

3. **Firewall настройки**:

```bash
# UFW
ufw allow 22/tcp    # SSH
ufw allow 51820/udp # WireGuard
ufw allow 443/tcp   # VLESS
ufw enable
```

4. **Храните приватные ключи в .env**, не коммитьте их в git

---

## 🧪 Тестирование

### Проверка SSH подключения:

```bash
# С вашего компьютера
ssh -i ~/.ssh/ghettovpn_bot root@your-vps-ip "wg show"
```

Должен вернуть информацию о WireGuard интерфейсе.

### Проверка через бота:

1. Откройте админ-панель в боте
2. Серверы → Выберите сервер
3. Нажмите **🔄 Проверить**

Бот выполнит health check:
- Проверит SSH подключение
- Проверит статус WireGuard/Xray
- Покажет количество подключенных пользователей
- Покажет использование CPU/RAM

---

## 📈 Мониторинг

### Автоматический мониторинг:

Бот автоматически каждые 5 минут:
- ✅ Проверяет доступность серверов
- ✅ Обновляет статистику нагрузки
- ✅ Считает активных пользователей
- ✅ Уведомляет админов о проблемах

### Ручная проверка:

Через админ-панель → Серверы → 📊 Статистика

---

## 🐛 Troubleshooting

### Ошибка: "SSH connection failed"

**Причина**: Неправильные SSH credentials или firewall блокирует

**Решение**:
```bash
# Проверьте SSH вручную
ssh -i ~/.ssh/ghettovpn_bot root@your-vps-ip

# Проверьте firewall
ufw status

# Проверьте SSH логи на VPS
tail -f /var/log/auth.log
```

### Ошибка: "Permission denied"

**Причина**: У пользователя нет прав на выполнение команд

**Решение**:
```bash
# Дайте права пользователю
usermod -aG sudo ghettovpn-bot

# Или добавьте в sudoers
visudo
# Добавьте: ghettovpn-bot ALL=(ALL) NOPASSWD: /usr/bin/wg, /usr/bin/systemctl
```

### Ошибка: "WireGuard not found"

**Причина**: WireGuard не установлен или не в PATH

**Решение**:
```bash
# Установите WireGuard
apt install -y wireguard wireguard-tools

# Проверьте путь
which wg
which wg-quick
```

### Ошибка: "Failed to add peer"

**Причина**: Неправильный формат конфига или синтаксис

**Решение**:
```bash
# Проверьте конфиг вручную
wg show wg0

# Проверьте синтаксис
wg-quick strip wg0

# Перезапустите WireGuard
systemctl restart wg-quick@wg0
```

---

## 💡 Продвинутая настройка

### Использование нескольких серверов:

Просто добавьте все ваши VPS через админ-панель. Бот будет автоматически:
- Распределять нагрузку
- Выбирать наименее загруженный сервер
- Переключать пользователей при проблемах

### Автоматическая синхронизация:

Включите в конфиге сервера:
```json
{
  "ssh_enabled": true,
  "auto_sync": true,
  "sync_interval": 3600
}
```

Бот будет каждый час:
- Проверять активные подключения
- Удалять неактивных пользователей
- Очищать старые конфиги

---

## 📝 Примеры конфигураций

### Для нескольких серверов в одной админке:

```
Сервер 1:
  Название: US-East-1
  IP: 1.2.3.4
  Протокол: WireGuard
  SSH: root + ключ

Сервер 2:
  Название: EU-Germany-1
  IP: 5.6.7.8
  Протокол: VLESS
  SSH: ghettovpn-bot + ключ

Сервер 3:
  Название: Asia-Singapore-1
  IP: 9.10.11.12
  Протокол: WireGuard
  SSH: root + пароль (временно)
```

---

## ✅ Checklist настройки

- [ ] VPS сервер арендован
- [ ] WireGuard/Xray установлен и запущен
- [ ] SSH ключи сгенерированы
- [ ] SSH доступ настроен и протестирован
- [ ] Firewall настроен (порты открыты)
- [ ] Сервер добавлен в админ-панель бота
- [ ] Health check проходит успешно
- [ ] Тестовый пользователь создан и подключен
- [ ] Мониторинг работает
- [ ] Автоудаление старых ключей работает

---

## 🎯 Готово!

Теперь ваш GHETTO VPN полностью автоматизирован. Бот сам будет управлять всеми ключами на ваших VPS серверах через SSH!

**Никаких ручных действий не требуется!** 🚀

---

Создано: 30.06.2026  
Версия: 2.0.0 (SSH Integration)
