"""
Server Pydantic Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from src.domain.models import ServerStatus, VPNProtocol


# ============================================================================
# BASE SCHEMAS
# ============================================================================

class ServerBase(BaseModel):
    """Base server schema"""
    code: str = Field(..., max_length=20, description="Server code (e.g., US-NY)")
    name: str = Field(..., max_length=255)
    country: str = Field(..., max_length=100)
    country_code: str = Field(..., max_length=2, description="ISO 3166-1 alpha-2")
    city: str = Field(..., max_length=100)
    ip_address: str = Field(..., max_length=45)
    port: int = Field(..., gt=0, le=65535)
    protocol: VPNProtocol


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ServerCreate(ServerBase):
    """Schema for creating server"""
    max_users: int = Field(default=1000, gt=0)
    bandwidth_limit_mbps: Optional[float] = None
    config: Optional[Dict[str, Any]] = None
    priority: int = Field(default=100, ge=0)


class ServerUpdate(BaseModel):
    """Schema for updating server"""
    name: Optional[str] = Field(None, max_length=255)
    status: Optional[ServerStatus] = None
    is_active: Optional[bool] = None
    max_users: Optional[int] = Field(None, gt=0)
    bandwidth_limit_mbps: Optional[float] = None
    config: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=0)
    
    model_config = ConfigDict(use_enum_values=True)


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ServerResponse(ServerBase):
    """Schema for server response"""
    id: int
    status: ServerStatus
    is_active: bool
    load_percentage: float
    ping_ms: Optional[int] = None
    max_users: int
    current_users: int
    bandwidth_limit_mbps: Optional[float] = None
    bandwidth_used_gb: float
    config: Optional[Dict[str, Any]] = None
    priority: int
    created_at: datetime
    updated_at: datetime
    last_check: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ServerPublicResponse(BaseModel):
    """Public server info for users"""
    id: int
    code: str
    name: str
    country: str
    country_code: str
    city: str
    protocol: VPNProtocol
    status: ServerStatus
    load_percentage: float
    ping_ms: Optional[int] = None
    is_premium: bool = False
    
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class ServerListResponse(BaseModel):
    """Paginated server list"""
    items: List[ServerResponse]
    total: int
    skip: int
    limit: int


class ServerPublicListResponse(BaseModel):
    """Public server list for users"""
    items: List[ServerPublicResponse]
    total: int


class ServerStatsResponse(BaseModel):
    """Server statistics"""
    total_servers: int
    online_servers: int
    offline_servers: int
    total_bandwidth_gb: float
    average_load: float
    total_users_connected: int
