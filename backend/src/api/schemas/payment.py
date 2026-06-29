"""
Payment Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from src.domain.models import PaymentStatus, PaymentProvider, SubscriptionPlan


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class PaymentBase(BaseModel):
    """Base payment schema"""
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    provider: PaymentProvider


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class PaymentCreate(PaymentBase):
    """Schema for creating payment"""
    user_id: int
    plan: SubscriptionPlan
    promo_code: Optional[str] = None
    description: Optional[str] = None


class PaymentWebhook(BaseModel):
    """Payment webhook from provider"""
    external_id: str
    status: PaymentStatus
    amount: float
    currency: str
    metadata: Optional[Dict[str, Any]] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class PaymentResponse(PaymentBase):
    """Schema for payment response"""
    id: int
    user_id: int
    status: PaymentStatus
    external_id: Optional[str] = None
    invoice_id: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class PaymentListResponse(BaseModel):
    """Paginated payment list"""
    items: List[PaymentResponse]
    total: int
    skip: int
    limit: int


class PaymentInitResponse(BaseModel):
    """Payment initialization response"""
    payment_id: int
    checkout_url: str
    invoice_id: Optional[str] = None
    amount: float
    currency: str
    expires_at: Optional[datetime] = None


class PaymentStatsResponse(BaseModel):
    """Payment statistics"""
    total_revenue: float
    total_payments: int
    successful_payments: int
    failed_payments: int
    pending_payments: int
    revenue_by_plan: Dict[str, float]
    revenue_by_provider: Dict[str, float]
    today_revenue: float
    this_month_revenue: float


class PaymentProviderInfo(BaseModel):
    """Payment provider information"""
    provider: PaymentProvider
    name: str
    enabled: bool
    supported_currencies: List[str]
    min_amount: float
    max_amount: Optional[float] = None
    
    model_config = ConfigDict(use_enum_values=True)


class PaymentProvidersResponse(BaseModel):
    """Available payment providers"""
    providers: List[PaymentProviderInfo]
