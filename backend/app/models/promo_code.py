"""
GHETTO VPN - PromoCode Model
Represents promotional discount codes
"""

from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
import enum

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    Numeric,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.admin import Admin
    from app.models.payment import Payment


class PromoDiscountType(str, enum.Enum):
    """Promo code discount types"""
    PERCENTAGE = "percentage"  # e.g., 20% off
    FIXED_AMOUNT = "fixed_amount"  # e.g., $10 off
    FREE_DAYS = "free_days"  # e.g., +7 days


class PromoCode(Base):
    """Promotional code model"""
    
    __tablename__ = "promo_codes"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Code details
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Discount configuration
    discount_type: Mapped[PromoDiscountType] = mapped_column(
        SQLEnum(PromoDiscountType, name="promo_discount_type"),
        nullable=False
    )
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Usage limitations
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL = unlimited
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_uses_per_user: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    min_purchase_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Plan restrictions
    applicable_plans: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True
    )  # NULL = all plans
    
    # User restrictions
    user_whitelist: Mapped[list[int] | None] = mapped_column(
        ARRAY(Integer),
        nullable=True
    )  # Specific user IDs (NULL = all users)
    
    # Validity period
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Creator
    created_by_admin_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("admins.id", ondelete="SET NULL"),
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
    created_by: Mapped["Admin | None"] = relationship("Admin", back_populates="promo_codes")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="promo_code")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("discount_value > 0", name="check_discount_value_positive"),
        CheckConstraint(
            "(discount_type != 'percentage') OR (discount_value > 0 AND discount_value <= 100)",
            name="check_percentage_range"
        ),
        CheckConstraint(
            "current_uses <= COALESCE(max_uses, current_uses)",
            name="check_uses"
        ),
        Index("idx_promo_codes_code", func.upper(code), unique=True),
        Index("idx_promo_codes_valid_period", "valid_from", "valid_until"),
    )
    
    def __repr__(self) -> str:
        return f"<PromoCode(id={self.id}, code={self.code}, discount={self.discount_value}, type={self.discount_type.value})>"
    
    @property
    def is_valid(self) -> bool:
        """Check if promo code is currently valid"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        
        # Check valid_from
        if self.valid_from and now < self.valid_from:
            return False
        
        # Check valid_until
        if self.valid_until and now > self.valid_until:
            return False
        
        # Check max uses
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    @property
    def remaining_uses(self) -> int | None:
        """Get remaining uses (None if unlimited)"""
        if self.max_uses is None:
            return None
        return max(0, self.max_uses - self.current_uses)
    
    @property
    def usage_percentage(self) -> float | None:
        """Get usage percentage (None if unlimited)"""
        if self.max_uses is None:
            return None
        if self.max_uses == 0:
            return 100.0
        return (self.current_uses / self.max_uses) * 100
    
    def calculate_discount(self, amount: Decimal) -> Decimal:
        """
        Calculate discount amount for given purchase amount
        
        Args:
            amount: Purchase amount
            
        Returns:
            Discount amount
        """
        if self.discount_type == PromoDiscountType.PERCENTAGE:
            return amount * (self.discount_value / 100)
        elif self.discount_type == PromoDiscountType.FIXED_AMOUNT:
            return min(self.discount_value, amount)
        else:  # FREE_DAYS
            return Decimal("0.00")
    
    def is_applicable_for_plan(self, plan_type: str) -> bool:
        """
        Check if promo code is applicable for given plan
        
        Args:
            plan_type: Subscription plan type
            
        Returns:
            True if applicable
        """
        if self.applicable_plans is None:
            return True
        return plan_type in self.applicable_plans
    
    def is_applicable_for_user(self, user_id: int) -> bool:
        """
        Check if promo code is applicable for given user
        
        Args:
            user_id: User ID
            
        Returns:
            True if applicable
        """
        if self.user_whitelist is None:
            return True
        return user_id in self.user_whitelist
