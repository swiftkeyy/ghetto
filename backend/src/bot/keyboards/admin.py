"""
Admin Keyboards - Inline keyboards for admin panel in bot
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
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
        InlineKeyboardButton(text="🎟️ Промокоды", callback_data="admin_promo"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_panel")
    )
    
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_admin_users_menu() -> InlineKeyboardMarkup:
    """Меню управления пользователями"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_search_user")
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_users_stats"),
        InlineKeyboardButton(text="📋 Топ-10", callback_data="admin_users_top")
    )
    
    builder.row(
        InlineKeyboardButton(text="⚠️ Проблемные", callback_data="admin_users_problems")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    )
    
    return builder.as_markup()


def get_user_management_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления конкретным пользователем"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="💎 Выдать подписку",
            callback_data=f"admin_user_grant_{user_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🚫 Заблокировать",
            callback_data=f"admin_user_block_{user_id}"
        ),
        InlineKeyboardButton(
            text="✅ Разблокировать",
            callback_data=f"admin_user_unblock_{user_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📱 Устройства",
            callback_data=f"admin_user_devices_{user_id}"
        ),
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data=f"admin_user_stats_{user_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="💬 Написать",
            callback_data=f"admin_user_message_{user_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"admin_user_delete_{user_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_users")
    )
    
    return builder.as_markup()


def get_admin_servers_menu() -> InlineKeyboardMarkup:
    """Меню управления серверами"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="➕ Добавить сервер", callback_data="admin_server_add")
    )
    
    builder.row(
        InlineKeyboardButton(text="📋 Список серверов", callback_data="admin_servers_list"),
        InlineKeyboardButton(text="🔄 Health Check", callback_data="admin_servers_health")
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_servers_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    )
    
    return builder.as_markup()


def get_server_management_keyboard(server_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления конкретным сервером"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"admin_server_edit_{server_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔄 Проверить",
            callback_data=f"admin_server_check_{server_id}"
        ),
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data=f"admin_server_stats_{server_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="⏸️ Отключить",
            callback_data=f"admin_server_disable_{server_id}"
        ),
        InlineKeyboardButton(
            text="▶️ Включить",
            callback_data=f"admin_server_enable_{server_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🔑 Синхронизировать ключи",
            callback_data=f"admin_server_sync_{server_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"admin_server_delete_{server_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_servers")
    )
    
    return builder.as_markup()


def get_admin_subscriptions_menu() -> InlineKeyboardMarkup:
    """Меню управления подписками"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_subs_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="⏰ Истекающие", callback_data="admin_subs_expiring"),
        InlineKeyboardButton(text="✅ Активные", callback_data="admin_subs_active")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    )
    
    return builder.as_markup()


def get_admin_payments_menu() -> InlineKeyboardMarkup:
    """Меню управления платежами"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="💰 Статистика", callback_data="admin_payments_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="✅ Завершенные", callback_data="admin_payments_completed"),
        InlineKeyboardButton(text="⏳ Ожидающие", callback_data="admin_payments_pending")
    )
    
    builder.row(
        InlineKeyboardButton(text="❌ Ошибки", callback_data="admin_payments_failed")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    )
    
    return builder.as_markup()


def get_admin_promo_menu() -> InlineKeyboardMarkup:
    """Меню управления промокодами"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_promo_create")
    )
    
    builder.row(
        InlineKeyboardButton(text="📋 Активные", callback_data="admin_promo_active"),
        InlineKeyboardButton(text="🚫 Неактивные", callback_data="admin_promo_inactive")
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_promo_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    )
    
    return builder.as_markup()


def get_admin_stats_menu() -> InlineKeyboardMarkup:
    """Меню статистики"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_stats_users"),
        InlineKeyboardButton(text="💰 Доходы", callback_data="admin_stats_revenue")
    )
    
    builder.row(
        InlineKeyboardButton(text="🌍 Серверы", callback_data="admin_stats_servers"),
        InlineKeyboardButton(text="📱 Устройства", callback_data="admin_stats_devices")
    )
    
    builder.row(
        InlineKeyboardButton(text="🎁 Рефералы", callback_data="admin_stats_referrals")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")
    )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")
    )
    
    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение рассылки"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📢 Всем", callback_data="broadcast_all")
    )
    
    builder.row(
        InlineKeyboardButton(text="💎 Только Premium", callback_data="broadcast_premium"),
        InlineKeyboardButton(text="🆓 Только Free", callback_data="broadcast_free")
    )
    
    builder.row(
        InlineKeyboardButton(text="✅ Активным", callback_data="broadcast_active")
    )
    
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_panel")
    )
    
    return builder.as_markup()
