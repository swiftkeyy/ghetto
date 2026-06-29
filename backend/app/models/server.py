"""
GHETTO VPN - Server Model
Represents VPN servers with multi-protocol support
"""

from datetime import datetime
from typing import TYPE_CHECKING
import enum

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    Enum as SQLEnum,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.connection import Connection


class ServerStatus(str, enum.Enum):
    """Server status types"""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class Server(Base):
    """VPN Server model with multi-protocol support"""
    
    __tablename__ = "servers"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Location
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)  # ISO 3166-1 alpha-2
    country_name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Server details
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    public_ip: Mapped[str] = mapped_column(INET, nullable=False)
    management_port: Mapped[int] = mapped_column(Integer, default=22, nullable=False)
    
    # Protocol support flags
    supports_wireguard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_vless: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_xray: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_singbox: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_outline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # WireGuard configuration
    wireguard_port: Mapped[int] = mapped_column(Integer, default=51820, nullable=False)
    wireguard_public_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    wireguard_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    wireguard_allowed_ips: Mapped[str] = mapped_column(
        Text,
        default="0.0.0.0/0, ::/0",
        nullable=False
    )
    
    # VLESS Reality configuration
    vless_port: Mapped[int] = mapped_column(Integer, default=443, nullable=False)
    vless_uuid: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    vless_reality_public_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    vless_reality_short_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    vless_reality_server_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Xray configuration
    xray_port: Mapped[int] = mapped_column(Integer, default=443, nullable=False)
    xray_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # sing-box configuration
    singbox_port: Mapped[int] = mapped_column(Integer, default=443, nullable=False)
    singbox_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    # Outline configuration
    outline_api_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    outline_cert_sha256: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Status & monitoring
    status: Mapped[ServerStatus] = mapped_column(
        SQLEnum(ServerStatus, name="server_status"),
        default=ServerStatus.ONLINE,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_recommended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    
    # Performance metrics
    load_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    ping_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bandwidth_mbps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_users: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    current_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Features
    supports_p2p: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_torrenting: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    last_health_check: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    devices: Mapped[list["Device"]] = relationship(
        "Device",
        back_populates="server",
        cascade="all, delete-orphan"
    )
    
    connections: Mapped[list["Connection"]] = relationship(
        "Connection",
        back_populates="server",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("load_percentage >= 0 AND load_percentage <= 100", name="check_load_percentage"),
        CheckConstraint("current_users >= 0", name="check_current_users_positive"),
        CheckConstraint("max_users > 0", name="check_max_users_positive"),
        Index("idx_servers_country_active", "country_code", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Server(id={self.id}, name={self.name}, country={self.country_code}, status={self.status.value})>"
    
    @property
    def is_online(self) -> bool:
        """Check if server is online"""
        return self.status == ServerStatus.ONLINE and self.is_active
    
    @property
    def is_overloaded(self) -> bool:
        """Check if server is overloaded"""
        return self.load_percentage > 80 or self.current_users >= self.max_users
    
    @property
    def load_status(self) -> str:
        """Get load status string"""
        if self.load_percentage < 30:
            return "low"
        elif self.load_percentage < 70:
            return "medium"
        else:
            return "high"
    
    @property
    def display_name(self) -> str:
        """Get display name with flag emoji"""
        country_flags = {
            "US": "🇺🇸", "GB": "🇬🇧", "DE": "🇩🇪", "FR": "🇫🇷", "NL": "🇳🇱",
            "SG": "🇸🇬", "JP": "🇯🇵", "CA": "🇨🇦", "AU": "🇦🇺", "RU": "🇷🇺",
            "UA": "🇺🇦", "PL": "🇵🇱", "ES": "🇪🇸", "IT": "🇮🇹", "SE": "🇸🇪",
        }
        flag = country_flags.get(self.country_code, "🌍")
        city_part = f" - {self.city}" if self.city else ""
        return f"{flag} {self.name}{city_part}"
