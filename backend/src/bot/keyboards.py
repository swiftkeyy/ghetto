"""
Telegram Bot Inline Keyboards
Premium Design - Dark Elite Luxury Style
"""

from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.domain.models import Server, Device, SubscriptionPlan


# ============================================================================
# MAIN MENU
# ============================================================================

def get_main_menu_keyboard(is_premium: bool = False, is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Главное меню - премиум inline клавиатура
    """
    builder = InlineKeyboardBuilder()
    
    # Быстрое подключение (если премиум)
    if is_premium:
        builder.row(
            InlineKeyboardButton(
                text="🚀 Быстрое подключение",
                callback_data="quick_connect"
            )
        )
    
    # Основные кнопки
    builder.row(
        InlineKeyboardButton(text="🌍 Серверы", callback_data="servers"),
        InlineKeyboardButton(text="📱 Устройства", callback_data="devices")
    )
    
    builder.row(
        InlineKeyboardButton(text="💎 Подписки", callback_data="subscriptions"),
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
        InlineKeyboardButton(text="🎁 Рефералы", callback_data="referrals")
    )
    
    builder.row(
        InlineKeyboardButton(text="⚙ Настройки", callback_data="settings"),
        InlineKeyboardButton(text="🛟 Поддержка", callback_data="support")
    )
    
    # Админ панель
    if is_admin:
        builder.row(
            InlineKeyboardButton(
                text="⚡ Админ-панель",
                callback_data="admin_panel"
            )
        )
    
    return builder.as_markup()


# ============================================================================
# SERVERS
# ============================================================================

def get_servers_keyboard(servers: List[Server], page: int = 1, per_page: int = 5) -> InlineKeyboardMarkup:
    """
    Список серверов с пагинацией
    """
    builder = InlineKeyboardBuilder()
    
    start = (page - 1) * per_page
    end = start + per_page
    page_servers = servers[start:end]
    
    for server in page_servers:
        # Эмодзи флага (можно расширить)
        flag_emoji = get_country_flag(server.country_code)
        
        # Статус сервера
        status_emoji = "🟢" if server.status.value == "online" else "🔴"
        
        # Нагрузка
        load_emoji = get_load_emoji(server.load_percentage)
        
        text = f"{flag_emoji} {server.country} - {server.city} {status_emoji} {load_emoji}"
        
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"server:{server.id}"
            )
        )
    
    # Пагинация
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"servers_page:{page-1}")
        )
    
    total_pages = (len(servers) + per_page - 1) // per_page
    if page < total_pages:
        pagination_buttons.append(
            InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"servers_page:{page+1}")
        )
    
    if pagination_buttons:
        builder.row(*pagination_buttons)
    
    # Кнопка назад
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_server_details_keyboard(server_id: int, is_connected: bool = False) -> InlineKeyboardMarkup:
    """
    Детали сервера
    """
    builder = InlineKeyboardBuilder()
    
    if not is_connected:
        builder.row(
            InlineKeyboardButton(
                text="⚡ Подключиться",
                callback_data=f"connect_server:{server_id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="🔌 Отключиться",
                callback_data=f"disconnect_server:{server_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="⭐ В избранное", callback_data=f"favorite:{server_id}"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_server:{server_id}")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад к списку", callback_data="servers")
    )
    
    return builder.as_markup()


# ============================================================================
# DEVICE PLATFORM SELECTION
# ============================================================================

def get_platform_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Выбор платформы устройства - 4 большие карточки
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📱 Android (Happ)",
            callback_data="platform:android"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🍎 iOS / iPad (Happ)",
            callback_data="platform:ios"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📺 Android TV (Happ)",
            callback_data="platform:android_tv"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="💻 Windows (Hiddify)",
            callback_data="platform:windows"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="devices")
    )
    
    return builder.as_markup()


def get_device_config_keyboard(device_id: int, platform: str) -> InlineKeyboardMarkup:
    """
    Управление конфигом устройства
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить конфиг",
            callback_data=f"refresh_config:{device_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📋 Копировать ссылку",
            callback_data=f"copy_link:{device_id}"
        ),
        InlineKeyboardButton(
            text="📥 Скачать",
            callback_data=f"download_config:{device_id}"
        )
    )
    
    # Ссылка на приложение
    app_link = get_app_download_link(platform)
    if app_link:
        builder.row(
            InlineKeyboardButton(
                text="📲 Скачать приложение",
                url=app_link
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="📖 Инструкция", callback_data=f"instructions:{platform}")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="devices")
    )
    
    return builder.as_markup()


def get_devices_list_keyboard(devices: List[Device], max_devices: int) -> InlineKeyboardMarkup:
    """
    Список устройств пользователя
    """
    builder = InlineKeyboardBuilder()
    
    for device in devices:
        status_emoji = "🟢" if device.is_connected else "⚪"
        platform_emoji = get_platform_emoji(device.platform.value)
        
        builder.row(
            InlineKeyboardButton(
                text=f"{platform_emoji} {device.name} {status_emoji}",
                callback_data=f"device:{device.id}"
            )
        )
    
    # Добавить устройство
    if len(devices) < max_devices:
        builder.row(
            InlineKeyboardButton(
                text="➕ Добавить устройство",
                callback_data="add_device"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=f"⚠️ Лимит устройств ({len(devices)}/{max_devices})",
                callback_data="device_limit_info"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


# ============================================================================
# SUBSCRIPTIONS
# ============================================================================

def get_subscription_plans_keyboard(has_trial: bool = True) -> InlineKeyboardMarkup:
    """
    Планы подписок - премиум карточки
    """
    builder = InlineKeyboardBuilder()
    
    # Trial (если доступен)
    if has_trial:
        builder.row(
            InlineKeyboardButton(
                text="🎁 3 дня бесплатно (Trial)",
                callback_data="subscribe:trial"
            )
        )
    
    # 1 месяц
    builder.row(
        InlineKeyboardButton(
            text="💎 1 месяц - $9.99",
            callback_data="subscribe:1_month"
        )
    )
    
    # 3 месяца
    builder.row(
        InlineKeyboardButton(
            text="💎 3 месяца - $24.99 (скидка 17%)",
            callback_data="subscribe:3_months"
        )
    )
    
    # 6 месяцев
    builder.row(
        InlineKeyboardButton(
            text="💎 6 месяцев - $44.99 (скидка 25%)",
            callback_data="subscribe:6_months"
        )
    )
    
    # 12 месяцев (популярный)
    builder.row(
        InlineKeyboardButton(
            text="⭐ 12 месяцев - $79.99 (скидка 33%)",
            callback_data="subscribe:12_months"
        )
    )
    
    # Lifetime
    builder.row(
        InlineKeyboardButton(
            text="♾️ Навсегда - $299.99",
            callback_data="subscribe:lifetime"
        )
    )
    
    # Промокод
    builder.row(
        InlineKeyboardButton(
            text="🎟️ Ввести промокод",
            callback_data="enter_promo"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_payment_methods_keyboard(plan: str, amount: float) -> InlineKeyboardMarkup:
    """
    Выбор метода оплаты
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="💳 Банковская карта (Stripe)",
            callback_data=f"pay:stripe:{plan}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="₿ Криптовалюта",
            callback_data=f"pay:crypto:{plan}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🇷🇺 ЮKassa (RU)",
            callback_data=f"pay:yookassa:{plan}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="⭐ Telegram Stars",
            callback_data=f"pay:telegram:{plan}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="subscriptions")
    )
    
    return builder.as_markup()


# ============================================================================
# PROFILE
# ============================================================================

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """
    Меню профиля
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats"),
        InlineKeyboardButton(text="📱 Устройства", callback_data="devices")
    )
    
    builder.row(
        InlineKeyboardButton(text="💎 Подписка", callback_data="subscriptions"),
        InlineKeyboardButton(text="🌐 Язык", callback_data="change_language")
    )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


# ============================================================================
# REFERRALS
# ============================================================================

def get_referral_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    """
    Реферальная система
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📤 Поделиться ссылкой",
            url=f"https://t.me/share/url?url={referral_link}&text=Присоединяйся к GHETTO VPN!"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="📋 Копировать ссылку", callback_data="copy_referral"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="referral_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="🎁 Мои награды", callback_data="my_rewards")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


# ============================================================================
# SUPPORT
# ============================================================================

def get_support_keyboard() -> InlineKeyboardMarkup:
    """
    Меню поддержки
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="❓ FAQ", callback_data="faq")
    )
    
    builder.row(
        InlineKeyboardButton(text="📖 Инструкции", callback_data="instructions_menu")
    )
    
    builder.row(
        InlineKeyboardButton(text="💬 Написать в поддержку", callback_data="contact_support")
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📢 Telegram канал",
            url="https://t.me/ghettovpn"
        ),
        InlineKeyboardButton(
            text="💬 Чат",
            url="https://t.me/ghettovpn_chat"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


# ============================================================================
# ADMIN PANEL
# ============================================================================

def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """
    Админ панель
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton(text="🌍 Серверы", callback_data="admin_servers")
    )
    
    builder.row(
        InlineKeyboardButton(text="💎 Подписки", callback_data="admin_subscriptions"),
        InlineKeyboardButton(text="💰 Платежи", callback_data="admin_payments")
    )
    
    builder.row(
        InlineKeyboardButton(text="🎟️ Промокоды", callback_data="admin_promos"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🌐 Веб-панель",
            url="https://admin.ghettovpn.com"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    
    return builder.as_markup()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_country_flag(country_code: str) -> str:
    """Получить эмодзи флага по коду страны"""
    flags = {
        "US": "🇺🇸",
        "GB": "🇬🇧",
        "DE": "🇩🇪",
        "FR": "🇫🇷",
        "NL": "🇳🇱",
        "SG": "🇸🇬",
        "JP": "🇯🇵",
        "CA": "🇨🇦",
        "AU": "🇦🇺",
        "RU": "🇷🇺",
    }
    return flags.get(country_code.upper(), "🌍")


def get_load_emoji(load_percentage: float) -> str:
    """Получить эмодзи нагрузки"""
    if load_percentage < 30:
        return "🟢"
    elif load_percentage < 70:
        return "🟡"
    else:
        return "🔴"


def get_platform_emoji(platform: str) -> str:
    """Получить эмодзи платформы"""
    emojis = {
        "android": "📱",
        "ios": "🍎",
        "android_tv": "📺",
        "windows": "💻",
        "macos": "🖥️",
        "linux": "🐧",
    }
    return emojis.get(platform.lower(), "📱")


def get_app_download_link(platform: str) -> Optional[str]:
    """Получить ссылку на скачивание приложения"""
    links = {
        "android": "https://play.google.com/store/apps/details?id=app.hiddify.com",
        "ios": "https://apps.apple.com/app/hiddify/id6596777532",
        "android_tv": "https://play.google.com/store/apps/details?id=app.hiddify.com",
        "windows": "https://github.com/hiddify/hiddify-next/releases",
    }
    return links.get(platform.lower())


def get_back_button() -> InlineKeyboardMarkup:
    """Простая кнопка назад"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def get_cancel_button() -> InlineKeyboardMarkup:
    """Кнопка отмены"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()
