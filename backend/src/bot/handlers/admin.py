"""
Admin Panel Handlers - Full CRM in Telegram Bot
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from datetime import datetime, timedelta

from src.infrastructure.database import AsyncSessionLocal
from src.domain.models import User, Server, Subscription, Payment, PromoCode, Device
from src.bot.keyboards.admin import (
    get_admin_main_menu,
    get_admin_users_menu,
    get_admin_servers_menu,
    get_admin_subscriptions_menu,
    get_admin_payments_menu,
    get_admin_promo_menu,
    get_admin_stats_menu,
    get_user_management_keyboard,
    get_server_management_keyboard,
)
from src.api.dependencies.auth import get_user_by_telegram_id

router = Router()


# ============================================================================
# ADMIN MAIN MENU
# ============================================================================

@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    """Главное меню админ-панели"""
    async with AsyncSessionLocal() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        
        if not user or not user.is_admin:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        # Быстрая статистика
        query = select(func.count(User.id))
        total_users = await db.scalar(query)
        
        query = select(func.count(User.id)).where(User.is_premium == True)
        premium_users = await db.scalar(query)
        
        query = select(func.count(Server.id)).where(Server.status == "online")
        online_servers = await db.scalar(query)
        
        text = f"""
<b>⚡ Админ-панель GHETTO VPN</b>

<b>📊 Быстрая статистика:</b>
👥 Всего пользователей: <b>{total_users}</b>
💎 Premium: <b>{premium_users}</b>
🌍 Серверов онлайн: <b>{online_servers}</b>

<b>Выберите раздел управления:</b>
"""
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_main_menu()
        )
    
    await callback.answer()


# ============================================================================
# USERS MANAGEMENT
# ============================================================================

@router.callback_query(F.data == "admin_users")
async def admin_users_menu(callback: CallbackQuery):
    """Управление пользователями"""
    async with AsyncSessionLocal() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        
        if not user or not user.is_admin:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        # Статистика пользователей
        query = select(User).order_by(User.created_at.desc()).limit(10)
        result = await db.execute(query)
        recent_users = result.scalars().all()
        
        # Подсчет по статусам
        total = await db.scalar(select(func.count(User.id)))
        active = await db.scalar(select(func.count(User.id)).where(User.status == "active"))
        premium = await db.scalar(select(func.count(User.id)).where(User.is_premium == True))
        blocked = await db.scalar(select(func.count(User.id)).where(User.status == "blocked"))
        
        text = f"""
<b>👥 Управление пользователями</b>

<b>📊 Статистика:</b>
• Всего: <b>{total}</b>
• Активных: <b>{active}</b>
• Premium: <b>{premium}</b>
• Заблокировано: <b>{blocked}</b>

<b>🆕 Последние 5 пользователей:</b>
"""
        
        for u in recent_users[:5]:
            status_emoji = "💎" if u.is_premium else "🆓"
            text += f"\n{status_emoji} @{u.username or 'Unknown'} (ID: {u.telegram_id})"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_users_menu()
        )
    
    await callback.answer()


@router.callback_query(F.data == "admin_search_user")
async def admin_search_user_prompt(callback: CallbackQuery, state: FSMContext):
    """Запрос на поиск пользователя"""
    await state.set_state("waiting_user_search")
    
    await callback.message.edit_text(
        "<b>🔍 Поиск пользователя</b>\n\n"
        "Отправьте:\n"
        "• Username (без @)\n"
        "• Telegram ID\n"
        "• Имя пользователя\n\n"
        "Для отмены нажмите /cancel"
    )
    await callback.answer()


@router.message(F.text, lambda msg: msg.text and msg.text.startswith('/cancel') == False)
async def process_user_search(message: Message, state: FSMContext):
    """Обработка поиска пользователя"""
    current_state = await state.get_state()
    if current_state != "waiting_user_search":
        return
    
    search_query = message.text.strip()
    
    async with AsyncSessionLocal() as db:
        # Поиск по username, telegram_id или имени
        if search_query.isdigit():
            query = select(User).where(User.telegram_id == int(search_query))
        else:
            query = select(User).where(
                (User.username.ilike(f"%{search_query}%")) |
                (User.first_name.ilike(f"%{search_query}%"))
            ).limit(10)
        
        result = await db.execute(query)
        users = result.scalars().all()
        
        if not users:
            await message.answer(
                "❌ Пользователи не найдены\n\n"
                "Попробуйте другой запрос или /cancel для отмены"
            )
            return
        
        if len(users) == 1:
            # Показать детальную информацию
            u = users[0]
            await show_user_details(message, u, db)
            await state.clear()
        else:
            # Показать список найденных
            text = f"<b>🔍 Найдено пользователей: {len(users)}</b>\n\n"
            for u in users:
                status = "💎 Premium" if u.is_premium else "🆓 Free"
                text += f"{status} @{u.username or 'Unknown'}\n"
                text += f"   ID: <code>{u.telegram_id}</code>\n"
                text += f"   Имя: {u.first_name or 'N/A'}\n\n"
            
            text += "\nОтправьте точный ID для детальной информации"
            
            await message.answer(text)
    
    await state.clear()


async def show_user_details(message: Message, user: User, db):
    """Показать детальную информацию о пользователе"""
    
    # Подсчет устройств
    devices_count = await db.scalar(
        select(func.count(Device.id)).where(Device.user_id == user.id)
    )
    
    # Информация о подписке
    sub_text = "❌ Нет подписки"
    if user.subscription_end:
        days_left = (user.subscription_end - datetime.utcnow()).days
        if days_left > 0:
            sub_text = f"✅ Активна ({days_left} дн.)"
        else:
            sub_text = "⏰ Истекла"
    
    text = f"""
<b>👤 Информация о пользователе</b>

<b>📝 Основное:</b>
• ID: <code>{user.telegram_id}</code>
• Username: @{user.username or 'не указан'}
• Имя: {user.first_name or 'N/A'} {user.last_name or ''}
• Статус: {user.status.value}

<b>💎 Подписка:</b>
• Premium: {"✅ Да" if user.is_premium else "❌ Нет"}
• {sub_text}

<b>📊 Статистика:</b>
• Трафик: {user.total_bandwidth_used:.2f} GB
• Подключений: {user.total_connections}
• Устройств: {devices_count}

<b>🎁 Реферальная программа:</b>
• Код: <code>{user.referral_code}</code>

<b>📅 Даты:</b>
• Регистрация: {user.created_at.strftime('%d.%m.%Y')}
• Последняя активность: {user.last_activity.strftime('%d.%m.%Y %H:%M') if user.last_activity else 'N/A'}
"""
    
    await message.answer(
        text,
        reply_markup=get_user_management_keyboard(user.id)
    )


@router.callback_query(F.data.startswith("admin_user_"))
async def admin_user_action(callback: CallbackQuery):
    """Действия с пользователем"""
    action = callback.data.split("_")[2]  # admin_user_ACTION_ID
    user_id = int(callback.data.split("_")[3])
    
    async with AsyncSessionLocal() as db:
        admin = await get_user_by_telegram_id(callback.from_user.id, db)
        
        if not admin or not admin.is_admin:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        target_user = result.scalar_one_or_none()
        
        if not target_user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        if action == "block":
            target_user.status = "blocked"
            await db.commit()
            await callback.answer("✅ Пользователь заблокирован", show_alert=True)
        
        elif action == "unblock":
            target_user.status = "active"
            await db.commit()
            await callback.answer("✅ Пользователь разблокирован", show_alert=True)
        
        elif action == "grant":
            # Выдать подписку (запросить количество дней)
            await callback.message.edit_text(
                f"<b>💎 Выдать подписку</b>\n\n"
                f"Пользователь: @{target_user.username}\n\n"
                f"Отправьте количество дней (1-365):"
            )
            # TODO: Добавить FSM для ввода дней
        
        elif action == "delete":
            await db.delete(target_user)
            await db.commit()
            await callback.answer("✅ Пользователь удален", show_alert=True)
            await callback.message.edit_text("✅ Пользователь удален из системы")


# ============================================================================
# SERVERS MANAGEMENT
# ============================================================================

@router.callback_query(F.data == "admin_servers")
async def admin_servers_menu(callback: CallbackQuery):
    """Управление серверами"""
    async with AsyncSessionLocal() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        
        if not user or not user.is_admin:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        # Получить все серверы
        query = select(Server).order_by(Server.created_at.desc())
        result = await db.execute(query)
        servers = result.scalars().all()
        
        text = "<b>🌍 Управление серверами</b>\n\n"
        
        if not servers:
            text += "❌ Серверов пока нет\n\n"
            text += "Добавьте первый сервер через кнопку ниже"
        else:
            total = len(servers)
            online = sum(1 for s in servers if s.status.value == "online")
            
            text += f"<b>📊 Статистика:</b>\n"
            text += f"• Всего: <b>{total}</b>\n"
            text += f"• Онлайн: <b>{online}</b>\n"
            text += f"• Оффлайн: <b>{total - online}</b>\n\n"
            
            text += "<b>🖥️ Список серверов:</b>\n"
            for s in servers[:10]:
                status_emoji = "🟢" if s.status.value == "online" else "🔴"
                load_emoji = "🟢" if s.load_percentage < 50 else "🟡" if s.load_percentage < 80 else "🔴"
                
                text += f"\n{status_emoji} <b>{s.name}</b>\n"
                text += f"   📍 {s.city}, {s.country}\n"
                text += f"   {load_emoji} Нагрузка: {s.load_percentage}%\n"
                text += f"   👥 Пользователей: {s.current_users}/{s.max_users}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_servers_menu()
        )
    
    await callback.answer()


# ============================================================================
# STATISTICS
# ============================================================================

@router.callback_query(F.data == "admin_stats")
async def admin_statistics(callback: CallbackQuery):
    """Детальная статистика"""
    async with AsyncSessionLocal() as db:
        user = await get_user_by_telegram_id(callback.from_user.id, db)
        
        if not user or not user.is_admin:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        # Пользователи
        total_users = await db.scalar(select(func.count(User.id)))
        premium_users = await db.scalar(
            select(func.count(User.id)).where(User.is_premium == True)
        )
        
        # Новые за сегодня
        today = datetime.utcnow().date()
        today_users = await db.scalar(
            select(func.count(User.id)).where(
                func.date(User.created_at) == today
            )
        )
        
        # Платежи
        query = select(Payment).where(Payment.status == "completed")
        result = await db.execute(query)
        payments = result.scalars().all()
        
        total_revenue = sum(p.amount for p in payments)
        today_revenue = sum(
            p.amount for p in payments 
            if p.completed_at and p.completed_at.date() == today
        )
        
        # Серверы
        total_servers = await db.scalar(select(func.count(Server.id)))
        online_servers = await db.scalar(
            select(func.count(Server.id)).where(Server.status == "online")
        )
        
        text = f"""
<b>📊 Детальная статистика</b>

<b>👥 Пользователи:</b>
• Всего: <b>{total_users}</b>
• Premium: <b>{premium_users}</b> ({premium_users/total_users*100:.1f}%)
• Сегодня новых: <b>{today_users}</b>

<b>💰 Доходы:</b>
• Всего: <b>${total_revenue:.2f}</b>
• Сегодня: <b>${today_revenue:.2f}</b>
• Транзакций: <b>{len(payments)}</b>

<b>🌍 Серверы:</b>
• Всего: <b>{total_servers}</b>
• Онлайн: <b>{online_servers}</b>
• Оффлайн: <b>{total_servers - online_servers}</b>

<b>📅 Дата обновления:</b>
{datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC
"""
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_stats_menu()
        )
    
    await callback.answer()


# ============================================================================
# BROADCAST
# ============================================================================

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_menu(callback: CallbackQuery, state: FSMContext):
    """Меню рассылки"""
    user_obj = callback.from_user
    
    async with AsyncSessionLocal() as db:
        user = await get_user_by_telegram_id(user_obj.id, db)
        
        if not user or not user.is_admin:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
    
    await state.set_state("waiting_broadcast_message")
    
    text = """
<b>📢 Рассылка сообщений</b>

Отправьте сообщение для рассылки пользователям.

<b>Можно отправить:</b>
• Текст
• Фото с текстом
• Видео с текстом

После отправки вы сможете выбрать целевую аудиторию:
• Все пользователи
• Только Premium
• Только Free

Для отмены: /cancel
"""
    
    await callback.message.edit_text(text)
    await callback.answer()
