"""
Device Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from src.domain.models import DevicePlatform


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class DeviceBase(BaseModel):
    """Base device schema"""
    name: str = Field(..., max_length=255, description="Device name")
    platform: DevicePlatform


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class DeviceCreate(DeviceBase):
    """Schema for creating device"""
    user_id: int


class DeviceUpdate(BaseModel):
    """Schema for updating device"""
    name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class DeviceConfigRequest(BaseModel):
    """Request for device configuration"""
    server_id: int
    platform: DevicePlatform


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class DeviceResponse(DeviceBase):
    """Schema for device response"""
    id: int
    user_id: int
    device_id: str
    is_active: bool
    is_connected: bool
    total_bandwidth: float = Field(..., description="Total bandwidth in GB")
    last_ip: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_connection: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class DeviceConfigResponse(BaseModel):
    """Device configuration response"""
    config: str = Field(..., description="Base64 encoded configuration")
    qr_code: str = Field(..., description="Base64 encoded QR code image")
    import_link: str = Field(..., description="Deep link for app import")
    instructions: str = Field(..., description="Setup instructions")
    app_download_link: str


class DeviceListResponse(BaseModel):
    """User's device list"""
    items: List[DeviceResponse]
    total: int
    max_devices: int
    remaining_slots: int


class DeviceStatsResponse(BaseModel):
    """Device statistics"""
    device_id: int
    total_bandwidth_gb: float
    total_connections: int
    last_connected: Optional[datetime] = None
    average_session_duration_minutes: Optional[float] = None
