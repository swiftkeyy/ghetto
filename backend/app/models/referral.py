"""
GHETTO VPN - Referral Model
Represents referral system tracking
"""

from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
import enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    Numeric,
    Boolean,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.subscription import Subscription
    from app.models.payment import Payment


class ReferralRewardType(str, enum.Enum):
    """Referral reward types"""
    FREE_DAYS = "free_days"
    DISCOUNT_PERCENTAGE = "discount_percentage"
    CASHBACK = "cashback"


class ReferralRewardStatus(str, enum.Enum):
    """Referral reward status"""
    PENDING = "pending"
    EARNED = "earned"
    APPLIED = "applied"
    EXPIRED = "expired"


class Referral(Base):
    """Referral tracking model"""
    
    __tablename__ = "referrals"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign keys
    referrer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    referred_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Reward configuration
    reward_type: Mapped[ReferralRewardType] = mapped_column(
        SQLEnum(ReferralRewardType, name="referral_reward_type"),
        default=ReferralRewardType.FREE_DAYS,
        nullable=False
    )
    reward_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reward_status: Mapped[ReferralRewardStatus] = mapped_column(
        SQLEnum(ReferralRewardStatus, name="referral_reward_status"),
        default=ReferralRewardStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Tracking
    referred_registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    referred_subscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    referred_subscription_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True
    )
    referred_payment_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Reward details
    reward_earned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    reward_applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    reward_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
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
    
    # Relationships
    referrer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referrer_id],
        back_populates="referrals_made"
    )
    referred: Mapped["User"] = relationship(
        "User",
        foreign_keys=[referred_id],
        back_populates="referred_by"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("referrer_id != referred_id", name="check_different_users"),
        UniqueConstraint("referrer_id", "referred_id", name="uq_referrals_referrer_referred"),
        Index("idx_referrals_pending", "referrer_id", "reward_status", postgresql_where="reward_status = 'pending'"),
    )
    
    def __repr__(self) -> str:
        return f"<Referral(id={self.id}, referrer_id={self.referrer_id}, referred_id={self.referred_id}, status={self.reward_status.value})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if reward is pending"""
        return self.reward_status == ReferralRewardStatus.PENDING
    
    @property
    def is_earned(self) -> bool:
        """Check if reward is earned"""
        return self.reward_status == ReferralRewardStatus.EARNED
    
    @property
    def is_applied(self) -> bool:
        """Check if reward is applied"""
        return self.reward_status == ReferralRewardStatus.APPLIED
    
    @property
    def is_expired(self) -> bool:
        """Check if reward is expired"""
        if self.reward_expires_at is None:
            return False
        return datetime.utcnow() > self.reward_expires_at
