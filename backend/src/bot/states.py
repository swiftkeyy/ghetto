"""
Telegram Bot FSM States
"""

from aiogram.fsm.state import State, StatesGroup


class MainStates(StatesGroup):
    """Main menu states"""
    MAIN_MENU = State()


class SubscriptionStates(StatesGroup):
    """Subscription flow states"""
    SELECT_PLAN = State()
    ENTER_PROMO_CODE = State()
    CONFIRM_PAYMENT = State()
    PROCESSING_PAYMENT = State()


class ServerStates(StatesGroup):
    """Server selection states"""
    SELECT_SERVER = State()
    SELECT_PROTOCOL = State()
    SERVER_DETAILS = State()


class DeviceStates(StatesGroup):
    """Device management states"""
    SELECT_PLATFORM = State()
    DEVICE_LIST = State()
    DEVICE_DETAILS = State()
    ENTER_DEVICE_NAME = State()
    CONFIRM_DELETE = State()


class ProfileStates(StatesGroup):
    """Profile management states"""
    VIEW_PROFILE = State()
    EDIT_LANGUAGE = State()


class ReferralStates(StatesGroup):
    """Referral system states"""
    VIEW_STATS = State()
    VIEW_REWARDS = State()


class SupportStates(StatesGroup):
    """Support states"""
    SUPPORT_MENU = State()
    ENTER_MESSAGE = State()
    FAQ = State()


class AdminStates(StatesGroup):
    """Admin panel states"""
    ADMIN_MENU = State()
    MANAGE_USERS = State()
    MANAGE_SERVERS = State()
    MANAGE_PROMOS = State()
    BROADCAST = State()
    STATISTICS = State()
