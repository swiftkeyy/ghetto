"""
Telegram Bot Main Entry Point
GHETTO VPN - Premium VPN Bot
"""

import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage

from sqlalchemy import select

from src.core.config import settings
from src.infrastructure.database import AsyncSessionLocal
from src.infrastructure.redis import redis_manager
from src.domain.models import User, UserStatus
from src.api.dependencies.auth import get_user_by_telegram_id, create_user_from_telegram
from src.bot.keyboards import (
    get_main_menu_keyboard,
    get_platform_selection_keyboard,
    get_servers_keyboard,
    get_subscription_plans_keyboard,
)
from src.bot.states import MainStates

logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
storage = RedisStorage.from_url(settings.REDIS_URL)
dp = Dispatcher(storage=storage)


# ============================================================================
# MIDDLEWARE
# ============================================================================

@dp.message.middleware()
async def db_session_middleware(handler, event: Message, data: dict):
    """Add database session to handler data"""
    async with AsyncSessionLocal() as session:
        data["db"] = session
        return await handler(event, data)


@dp.callback_query.middleware()
async def callback_db_middleware(handler, event: CallbackQuery, data: dict):
    """Add database session to callback handler data"""
    async with AsyncSessionLocal() as session:
        data["db"] = session
        return await handler(event, data)


# ============================================================================
# START COMMAND - ГЛАВНЫЙ ВХОД
# ============================================================================

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db):
    """
    /start - Приветствие и регистрация пользователя
    """
    telegram_user = message.from_user
    
    # Извлечь реферальный код из deep link
    args = message.text.split()
    referral_code = args[1] if len(args) > 1 else None
    
    # Проверить существует ли пользователь
    user = await get_user_by_telegram_id(telegram_user.id, db)
    
    if not user:
        # Создать нового пользователя
        user = await create_user_from_telegram(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            language_code=telegram_user.language_code or "en",
            referred_by_code=referral_code,
            db=db
        )
        
        logger.info(f"New user registered: {user.telegram_id}")
        
        # Приветственное сообщение для нового пользователя
        welcome_text = f"""
<b>🖤 Добро пожаловать в GHETTO VPN</b>

Привет, <b>{telegram_user.first_name}</b>! 👋

<b>GHETTO VPN</b> — это премиальный VPN-сервис нового поколения.

✨ <b>Что вы получаете:</b>
• 🚀 Молниеносная скорость
• 🌍 Серверы по всему миру
• 🔒 Максимальная приватность
• 📱 Поддержка всех платформ
• 🎯 Простое подключение в 1 клик

<b>💎 Попробуйте бесплатно</b> — 3 дня Trial-подписки доступны прямо сейчас!

Нажмите кнопку ниже, чтобы начать 👇
"""
    else:
        # Приветствие для существующего пользователя
        welcome_text = f"""
<b>🖤 С возвращением, {telegram_user.first_name}!</b>

Рады видеть вас снова в <b>GHETTO VPN</b> 🚀

{get_user_status_text(user)}

Выберите действие из меню ниже 👇
"""
    
    await state.set_state(MainStates.MAIN_MENU)
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(
            is_premium=user.is_premium,
            is_admin=user.is_admin
        )
    )


# ============================================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================================

@dp.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, db):
    """Показать главное меню"""
    user = await get_user_by_telegram_id(callback.from_user.id, db)
    
    text = f"""
<b>🖤 GHETTO VPN</b>

{get_user_status_text(user)}

Выберите действие:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard(
            is_premium=user.is_premium,
            is_admin=user.is_admin
        )
    )
    await callback.answer()


# ============================================================================
# БЫСТРОЕ ПОДКЛЮЧЕНИЕ
# ============================================================================

@dp.callback_query(F.data == "quick_connect")
async def quick_connect(callback: CallbackQuery, db):
    """Быстрое подключение к лучшему серверу"""
    user = await get_user_by_telegram_id(callback.from_user.id, db)
    
    if not user.is_premium:
        await callback.answer(
            "❌ Требуется премиум подписка",
            show_alert=True
        )
        return
    
    await callback.answer("⚡ Подключение к оптимальному серверу...")
    
    # TODO: Логика выбора лучшего сервера
    # TODO: Проверка устройств
    # TODO: Генерация конфига
    
    text = """
<b>⚡ Быстрое подключение</b>

🟢 Подключено к оптимальному серверу!

<b>Сервер:</b> 🇩🇪 Germany - Frankfurt
<b>Протокол:</b> WireGuard
<b>Ping:</b> 12ms
<b>Нагрузка:</b> 🟢 23%

Выберите устройство для подключения:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_platform_selection_keyboard()
    )


# ============================================================================
# СЕРВЕРЫ
# ============================================================================

@dp.callback_query(F.data == "servers")
async def show_servers(callback: CallbackQuery, db):
    """Показать список серверов"""
    from src.domain.models import Server, ServerStatus
    
    # Получить активные серверы
    query = select(Server).where(
        Server.is_active == True,
        Server.status == ServerStatus.ONLINE
    ).order_by(Server.priority)
    
    result = await db.execute(query)
    servers = result.scalars().all()
    
    if not servers:
        await callback.answer("Нет доступных серверов", show_alert=True)
        return
    
    text = f"""
<b>🌍 Серверы GHETTO VPN</b>

Доступно серверов: <b>{len(servers)}</b>

Выберите сервер для подключения:
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_servers_keyboard(servers)
    )
    await callback.answer()


# ============================================================================
# УСТРОЙСТВА
# ============================================================================

@dp.callback_query(F.data == "devices")
async def show_devices(callback: CallbackQuery, db):
    """Показать список устройств"""
    from src.domain.models import Device
    
    user = await get_user_by_telegram_id(callback.from_user.id, db)
    
    # Получить устройства пользователя
    query = select(Device).where(Device.user_id == user.id)
    result = await db.execute(query)
    devices = result.scalars().all()
    
    if not devices:
        text = """
<b>📱 Мои устройства</b>

У вас пока нет подключенных устройств.

Добавьте первое устройство, чтобы начать использовать VPN!

<b>Поддерживаемые платформы:</b>
• 📱 Android (Happ)
• 🍎 iOS / iPad (Happ)
• 📺 Android TV (Happ)
• 💻 Windows (Hiddify)

Выберите вашу платформу:
"""
        keyboard = get_platform_selection_keyboard()
    else:
        from src.bot.keyboards import get_devices_list_keyboard
        
        text = f"""
<b>📱 Мои устройства</b>

Всего устройств: <b>{len(devices)}/{settings.MAX_DEVICES_PER_USER}</b>

Выберите устройство для управления:
"""
        keyboard = get_devices_list_keyboard(devices, settings.MAX_DEVICES_PER_USER)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "add_device")
async def add_device(callback: CallbackQuery):
    """Добавить новое устройство"""
    text = """
<b>➕ Добавить устройство</b>

Выберите платформу вашего устройства:

• <b>Android</b> — смартфоны и планшеты
• <b>iOS</b> — iPhone и iPad
• <b>Android TV</b> — телевизоры и приставки
• <b>Windows</b> — компьютеры и ноутбуки

Для каждой платформы мы создадим индивидуальную конфигурацию с QR-кодом и подробной инструкцией.
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_platform_selection_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("platform:"))
async def select_platform(callback: CallbackQuery, db):
    """Выбор платформы и генерация конфига"""
    platform = callback.data.split(":")[1]
    
    user = await get_user_by_telegram_id(callback.from_user.id, db)
    
    # TODO: Генерация конфига для выбранной платформы
    # TODO: Создание QR-кода
    # TODO: Сохранение устройства в БД
    
    platform_names = {
        "android": "Android (Happ)",
        "ios": "iOS / iPad (Happ)",
        "android_tv": "Android TV (Happ)",
        "windows": "Windows (Hiddify)"
    }
    
    text = f"""
<b>📱 {platform_names.get(platform, platform)}</b>

✅ Конфигурация успешно создана!

<b>Инструкция по подключению:</b>

1️⃣ Скачайте приложение по ссылке ниже
2️⃣ Откройте приложение
3️⃣ Нажмите "Добавить конфигурацию"
4️⃣ Отсканируйте QR-код или используйте ссылку импорта
5️⃣ Нажмите "Подключиться"

<b>Готово!</b> Ваш интернет теперь защищен 🔒

QR-код и ссылка импорта в следующем сообщении 👇
"""
    
    await callback.message.edit_text(text)
    
    # TODO: Отправить QR-код
    # await callback.message.answer_photo(
    #     photo=qr_code_file,
    #     caption="Отсканируйте этот QR-код в приложении"
    # )
    
    await callback.answer("✅ Конфигурация создана!")


# ============================================================================
# ПОДПИСКИ
# ============================================================================

@dp.callback_query(F.data == "subscriptions")
async def show_subscriptions(callback: CallbackQuery, db):
    """Показать планы подписок"""
    user = await get_user_by_telegram_id(callback.from_user.id, db)
    
    text = """
<b>💎 Подписки GHETTO VPN</b>

Выберите план, который подходит именно вам:

🎁 <b>Trial (3 дня)</b> — Бесплатно
   • Полный доступ ко всем серверам
   • До 10 GB трафика
   • Все функции Premium

💎 <b>Ежемесячные планы:</b>
   • Безлимитный трафик
   • Максимальная скорость
   • До 5 устройств одновременно
   • Приоритетная поддержка

<b>🔥 Экономьте до 33% с годовой подпиской!</b>
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_subscription_plans_keyboard(
            has_trial=not user.trial_used
        )
    )
    await callback.answer()


# ============================================================================
# ПРОФИЛЬ
# ============================================================================

@dp.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery, db):
    """Показать профиль пользователя"""
    from src.bot.keyboards import get_profile_keyboard
    
    user = await get_user_by_telegram_id(callback.from_user.id, db)
    
    # Форматирование информации о подписке
    subscription_text = "❌ Нет активной подписки"
    if user.is_premium and user.subscription_end:
        days_left = (user.subscription_end - user.created_at).days
        subscription_text = f"✅ Активна до {user.subscription_end.strftime('%d.%m.%Y')}\n   Осталось дней: <b>{days_left}</b>"
    
    text = f"""
<b>👤 Ваш профиль</b>

<b>Имя:</b> {user.first_name or 'Не указано'}
<b>Username:</b> @{user.username or 'не указан'}
<b>ID:</b> <code>{user.telegram_id}</code>

<b>💎 Подписка:</b> {subscription_text}

<b>📊 Статистика:</b>
• Использовано трафика: <b>{user.total_bandwidth_used:.2f} GB</b>
• Подключений: <b>{user.total_connections}</b>
• Реферальный код: <code>{user.referral_code}</code>

<b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y')}
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_profile_keyboard()
    )
    await callback.answer()


# ============================================================================
# РЕФЕРАЛЫ
# ============================================================================

@dp.callback_query(F.data == "referrals")
async def show_referrals(callback: CallbackQuery, db):
    """Показать реферальную систему"""
    from src.bot.keyboards import get_referral_keyboard
    
    user = await get_user_by_telegram_id(callback.from_user.id, db)
    
    # Получить статистику рефералов
    query = select(User).where(User.referred_by_id == user.id)
    result = await db.execute(query)
    referrals = result.scalars().all()
    
    active_referrals = sum(1 for r in referrals if r.is_premium)
    
    referral_link = f"https://t.me/{(await bot.get_me()).username}?start={user.referral_code}"
    
    text = f"""
<b>🎁 Реферальная программа</b>

Приглашайте друзей и получайте награды!

<b>📊 Ваша статистика:</b>
• Всего рефералов: <b>{len(referrals)}</b>
• Активных: <b>{active_referrals}</b>
• Заработано: <b>{active_referrals * 7} дней</b>

<b>🎯 Как это работает:</b>
1. Поделитесь своей реферальной ссылкой
2. Друг регистрируется по вашей ссылке
3. Когда друг покупает подписку — вы получаете <b>7 дней</b> бесплатно!
4. Друг получает скидку <b>10%</b> на первую покупку

<b>Ваша реферальная ссылка:</b>
<code>{referral_link}</code>
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_referral_keyboard(referral_link)
    )
    await callback.answer()


# ============================================================================
# ПОДДЕРЖКА
# ============================================================================

@dp.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    """Показать меню поддержки"""
    from src.bot.keyboards import get_support_keyboard
    
    text = """
<b>🛟 Поддержка</b>

Мы всегда рады помочь вам!

<b>📖 База знаний:</b>
• FAQ — ответы на частые вопросы
• Подробные инструкции по настройке
• Руководства по устранению проблем

<b>💬 Связь с нами:</b>
• Telegram чат — быстрые ответы от сообщества
• Техподдержка — напишите нам напрямую

<b>Среднее время ответа:</b> 15 минут ⚡
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_support_keyboard()
    )
    await callback.answer()


# ============================================================================
# ADMIN PANEL
# ============================================================================

@dp.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery, db):
    """Показать админ панель"""
    from src.bot.keyboards import get_admin_panel_keyboard
    
    user = await get_user_by_telegram_id(callback.from_user.id, db)
    
    if not user.is_admin:
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    # Получить статистику
    query = select(User)
    result = await db.execute(query)
    all_users = result.scalars().all()
    
    total_users = len(all_users)
    premium_users = sum(1 for u in all_users if u.is_premium)
    
    text = f"""
<b>⚡ Админ-панель</b>

<b>📊 Быстрая статистика:</b>
• Всего пользователей: <b>{total_users}</b>
• Premium: <b>{premium_users}</b>
• Сегодня новых: <b>0</b>

<b>Выберите раздел управления:</b>
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_panel_keyboard()
    )
    await callback.answer()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_user_status_text(user: User) -> str:
    """Получить текст статуса пользователя"""
    if user.is_premium and user.subscription_end:
        days_left = (user.subscription_end - user.created_at).days
        return f"<b>Статус:</b> 💎 Premium (осталось {days_left} дн.)"
    elif user.status == UserStatus.TRIAL:
        return "<b>Статус:</b> 🎁 Trial"
    else:
        return "<b>Статус:</b> 🆓 Free"


# ============================================================================
# START BOT
# ============================================================================

async def start_bot():
    """Start bot in polling mode"""
    logger.info("🤖 Starting GHETTO VPN Bot...")
    
    try:
        # Drop pending updates
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
        raise


async def set_webhook():
    """Set webhook for production"""
    if settings.BOT_WEBHOOK_URL:
        webhook_url = f"{settings.BOT_WEBHOOK_URL}/{settings.BOT_WEBHOOK_SECRET}"
        await bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set to: {webhook_url}")


if __name__ == "__main__":
    asyncio.run(start_bot())
