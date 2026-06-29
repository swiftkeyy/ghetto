"""
GHETTO VPN - SQLAlchemy Base
Import all models here for Alembic migrations
"""

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData


# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    metadata = metadata


# Import all models here so Alembic can detect them
from app.models.user import User  # noqa
from app.models.subscription import Subscription  # noqa
from app.models.server import Server  # noqa
from app.models.device import Device  # noqa
from app.models.payment import Payment  # noqa
from app.models.promo_code import PromoCode  # noqa
from app.models.referral import Referral  # noqa
from app.models.connection import Connection  # noqa
from app.models.admin import Admin  # noqa
from app.models.notification import Notification  # noqa
from app.models.audit_log import AuditLog  # noqa
