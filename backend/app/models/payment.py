"""
GHETTO VPN - Payment Model
Represents payment transactions and history
"""

from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
import enum

from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    DateTime,
    Text,
    Numeric,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.subscription import Subscription, SubscriptionPlanType
    from app.models.promo_code import PromoCode


class PaymentProvider(str, enum.Enum):
    """Payment provider types"""
    YOOKASSA = "yookassa"
    STRIPE = "stripe"
    CRYPTO_USDT = "crypto_usdt"
    CRYPTO_BTC = "crypto_btc"
    CRYPTO_ETH = "crypto_eth"


class PaymentStatus(str, enum.Enum):
    """Payment status types"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Payment(Base):
    """Payment transaction model"""
    
    __tablename__ = "payments"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subscription_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Payment details
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)  # ISO 4217
    provider: Mapped[PaymentProvider] = mapped_column(
        SQLEnum(PaymentProvider, name="payment_provider"),
        nullable=False,
        index=True
    )
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )
    provider_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Plan info (stored for history)
    plan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Discount
    promo_code_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("promo_codes.id", ondelete="SET NULL"),
        nullable=True
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False
    )
    final_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Status
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Additional data
    payment_method: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )  # e.g., 'bank_card', 'sbp', 'wallet'
    payment_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # URL for user to complete payment
    webhook_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Raw webhook data
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Custom metadata
    
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
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )  # Payment link expiration
    succeeded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
    subscription: Mapped["Subscription | None"] = relationship("Subscription", back_populates="payments")
    promo_code: Mapped["PromoCode | None"] = relationship("PromoCode", back_populates="payments")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "amount > 0 AND final_amount > 0 AND discount_amount >= 0",
            name="check_amounts_positive"
        ),
        CheckConstraint("final_amount <= amount", name="check_final_amount"),
        Index("idx_payments_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
        Index(
            "idx_payments_pending",
            "status",
            "created_at",
            postgresql_where="status = 'pending'"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.final_amount} {self.currency}, status={self.status.value})>"
    
    @property
    def is_completed(self) -> bool:
        """Check if payment is completed"""
        return self.status == PaymentStatus.SUCCEEDED
    
    @property
    def is_pending(self) -> bool:
        """Check if payment is pending"""
        return self.status == PaymentStatus.PENDING
    
    @property
    def discount_percentage(self) -> float:
        """Calculate discount percentage"""
        if self.amount == 0:
            return 0.0
        return float((self.discount_amount / self.amount) * 100)
    
    @property
    def provider_display_name(self) -> str:
        """Get provider display name"""
        names = {
            PaymentProvider.YOOKASSA: "ЮKassa",
            PaymentProvider.STRIPE: "Stripe",
            PaymentProvider.CRYPTO_USDT: "USDT",
            PaymentProvider.CRYPTO_BTC: "Bitcoin",
            PaymentProvider.CRYPTO_ETH: "Ethereum",
        }
        return names.get(self.provider, self.provider.value)
