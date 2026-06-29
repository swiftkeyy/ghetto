"""
GHETTO VPN - Subscription Model
Represents user subscription plans and status
"""

from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    Boolean,
    DateTime,
    Numeric,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.payment import Payment


class SubscriptionPlanType(str, enum.Enum):
    """Subscription plan types"""
    TRIAL = "trial"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    LIFETIME = "lifetime"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status types"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Subscription(Base):
    """Subscription model"""
    
    __tablename__ = "subscriptions"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Plan details
    plan_type: Mapped[SubscriptionPlanType] = mapped_column(
        SQLEnum(SubscriptionPlanType, name="subscription_plan_type"),
        nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus, name="subscription_status"),
        default=SubscriptionStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Duration
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    is_lifetime: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Limits
    traffic_limit_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL = unlimited
    traffic_used_gb: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.000"),
        nullable=False
    )
    device_limit: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    
    # Auto-renewal
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
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
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="subscription",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("traffic_used_gb >= 0", name="check_traffic_positive"),
        CheckConstraint("device_limit > 0", name="check_device_limit_positive"),
        Index("idx_subscriptions_expires_at", "expires_at", postgresql_where="status = 'active'"),
        Index("idx_subscriptions_active_user", "user_id", unique=True, postgresql_where="status = 'active'"),
    )
    
    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan_type.value}, status={self.status.value})>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return self.status == SubscriptionStatus.ACTIVE
    
    @property
    def is_expired(self) -> bool:
        """Check if subscription has expired"""
        if self.is_lifetime:
            return False
        if self.expires_at is None:
            return True
        return datetime.utcnow() > self.expires_at
    
    @property
    def days_remaining(self) -> int | None:
        """Get number of days remaining"""
        if self.is_lifetime:
            return None
        if self.expires_at is None:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def traffic_remaining_gb(self) -> Decimal | None:
        """Get remaining traffic in GB"""
        if self.traffic_limit_gb is None:
            return None  # Unlimited
        return max(Decimal("0"), Decimal(str(self.traffic_limit_gb)) - self.traffic_used_gb)
    
    @property
    def traffic_used_percentage(self) -> float | None:
        """Get traffic usage percentage"""
        if self.traffic_limit_gb is None:
            return None  # Unlimited
        if self.traffic_limit_gb == 0:
            return 100.0
        return float((self.traffic_used_gb / Decimal(str(self.traffic_limit_gb))) * 100)
