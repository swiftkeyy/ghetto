"""
User Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from src.domain.models import UserStatus


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base user schema"""
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    language_code: str = Field(default="en", max_length=10)


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class UserCreate(UserBase):
    """Schema for creating new user"""
    referral_code: Optional[str] = Field(None, description="Referral code used")


class UserUpdate(BaseModel):
    """Schema for updating user"""
    username: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    language_code: Optional[str] = Field(None, max_length=10)
    status: Optional[UserStatus] = None
    is_premium: Optional[bool] = None
    
    model_config = ConfigDict(use_enum_values=True)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    status: UserStatus
    is_admin: bool
    is_premium: bool
    subscription_end: Optional[datetime] = None
    trial_used: bool
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    referral_code: str
    referred_by_id: Optional[int] = None
    total_bandwidth_used: float
    total_connections: int
    created_at: datetime
    updated_at: datetime
    last_activity: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserShortResponse(BaseModel):
    """Short user info"""
    id: int
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    is_premium: bool
    
    model_config = ConfigDict(from_attributes=True)


class UserStatsResponse(BaseModel):
    """User statistics"""
    total_bandwidth_used: float = Field(..., description="Total bandwidth in GB")
    total_connections: int
    active_devices: int
    active_subscription: bool
    subscription_days_left: Optional[int] = None


class UserListResponse(BaseModel):
    """Paginated user list response"""
    items: List[UserResponse]
    total: int
    skip: int
    limit: int
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# REFERRAL SCHEMAS
# ============================================================================

class ReferralStatsResponse(BaseModel):
    """Referral statistics"""
    total_referrals: int
    active_referrals: int
    total_earnings: float
    pending_rewards: int
    referral_link: str
