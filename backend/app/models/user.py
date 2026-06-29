"""
GHETTO VPN - User Model
Represents Telegram users in the system
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    String,
    Boolean,
    DateTime,
    Index,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.subscription import Subscription
    from app.models.device import Device
    from app.models.payment import Payment
    from app.models.referral import Referral
    from app.models.connection import Connection
    from app.models.notification import Notification


class User(Base):
    """User model for Telegram users"""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Telegram data
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    
    # Status flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Referral system
    referred_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    referral_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    devices: Mapped[list["Device"]] = relationship(
        "Device",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    connections: Mapped[list["Connection"]] = relationship(
        "Connection",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Referrals as referrer
    referrals_made: Mapped[list["Referral"]] = relationship(
        "Referral",
        foreign_keys="Referral.referrer_id",
        back_populates="referrer",
        cascade="all, delete-orphan"
    )
    
    # Referrals as referred
    referred_by: Mapped[list["Referral"]] = relationship(
        "Referral",
        foreign_keys="Referral.referred_id",
        back_populates="referred",
        cascade="all, delete-orphan"
    )
    
    # Self-referential relationship
    referrer: Mapped["User | None"] = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[referred_by_id]
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("telegram_id > 0", name="check_telegram_id_positive"),
        Index("idx_users_active", "is_active"),
        Index("idx_users_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username or f"User{self.telegram_id}"
    
    @property
    def has_active_subscription(self) -> bool:
        """Check if user has active subscription"""
        return any(sub.status == "active" for sub in self.subscriptions)
