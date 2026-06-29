"""
Subscription Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from src.domain.models import SubscriptionStatus, SubscriptionPlan


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class SubscriptionBase(BaseModel):
    """Base subscription schema"""
    plan: SubscriptionPlan
    price: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class SubscriptionCreate(SubscriptionBase):
    """Schema for creating subscription"""
    user_id: int
    start_date: datetime
    end_date: datetime
    promo_code: Optional[str] = None
    auto_renew: bool = False


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscription"""
    status: Optional[SubscriptionStatus] = None
    auto_renew: Optional[bool] = None
    end_date: Optional[datetime] = None
    
    model_config = ConfigDict(use_enum_values=True)


class SubscriptionExtend(BaseModel):
    """Schema for extending subscription"""
    days: int = Field(..., gt=0, description="Number of days to extend")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response"""
    id: int
    user_id: int
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime
    auto_renew: bool
    payment_id: Optional[int] = None
    promo_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class SubscriptionListResponse(BaseModel):
    """Paginated subscription list"""
    items: List[SubscriptionResponse]
    total: int
    skip: int
    limit: int


class SubscriptionPlanInfo(BaseModel):
    """Subscription plan information"""
    plan: SubscriptionPlan
    name: str
    duration_days: int
    price: float
    currency: str
    discount_percent: Optional[int] = None
    features: List[str]
    is_popular: bool = False
    
    model_config = ConfigDict(use_enum_values=True)


class SubscriptionPlansResponse(BaseModel):
    """All available subscription plans"""
    plans: List[SubscriptionPlanInfo]
    trial_available: bool
    trial_days: int
