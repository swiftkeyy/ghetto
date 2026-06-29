"""
GHETTO VPN - Device Model
Represents user devices with VPN configurations
"""

from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
import enum

from sqlalchemy import (
    BigInteger,
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
    computed_column,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.server import Server
    from app.models.connection import Connection


class DevicePlatform(str, enum.Enum):
    """Device platform types"""
    ANDROID = "android"
    IOS = "ios"
    ANDROID_TV = "android_tv"
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class VPNProtocol(str, enum.Enum):
    """VPN protocol types"""
    WIREGUARD = "wireguard"
    VLESS_REALITY = "vless_reality"
    XRAY = "xray"
    SINGBOX = "singbox"
    OUTLINE = "outline"


class Device(Base):
    """Device model for user VPN configurations"""
    
    __tablename__ = "devices"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    server_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("servers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Device info
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # User-defined name
    platform: Mapped[DevicePlatform] = mapped_column(
        SQLEnum(DevicePlatform, name="device_platform"),
        nullable=False,
        index=True
    )
    protocol: Mapped[VPNProtocol] = mapped_column(
        SQLEnum(VPNProtocol, name="vpn_protocol"),
        nullable=False,
        index=True
    )
    
    # VPN configuration
    config_data: Mapped[str] = mapped_column(Text, nullable=False)  # Full config (base64 encoded)
    config_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # Import URL (for one-tap)
    qr_code_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # Path to QR code image
    
    # WireGuard specific
    wireguard_public_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    wireguard_private_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # Encrypted
    wireguard_address: Mapped[str | None] = mapped_column(INET, nullable=True)  # Client IP in VPN network
    
    # VLESS/Xray specific
    vless_uuid: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    
    # sing-box specific
    singbox_uuid: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    
    # Outline specific
    outline_access_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Status & statistics
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    last_connection_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    last_disconnect_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    total_connections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Traffic statistics
    traffic_upload_gb: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.000"),
        nullable=False
    )
    traffic_download_gb: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        default=Decimal("0.000"),
        nullable=False
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
    user: Mapped["User"] = relationship("User", back_populates="devices")
    server: Mapped["Server | None"] = relationship("Server", back_populates="devices")
    
    connections: Mapped[list["Connection"]] = relationship(
        "Connection",
        back_populates="device",
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "traffic_upload_gb >= 0 AND traffic_download_gb >= 0",
            name="check_traffic_positive"
        ),
        Index(
            "idx_devices_wireguard_pubkey",
            "wireguard_public_key",
            unique=True,
            postgresql_where="wireguard_public_key IS NOT NULL"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Device(id={self.id}, name={self.name}, platform={self.platform.value}, protocol={self.protocol.value})>"
    
    @property
    def traffic_total_gb(self) -> Decimal:
        """Get total traffic used"""
        return self.traffic_upload_gb + self.traffic_download_gb
    
    @property
    def platform_emoji(self) -> str:
        """Get platform emoji"""
        emojis = {
            DevicePlatform.ANDROID: "📱",
            DevicePlatform.IOS: "🍎",
            DevicePlatform.ANDROID_TV: "📺",
            DevicePlatform.WINDOWS: "🪟",
            DevicePlatform.MACOS: "💻",
            DevicePlatform.LINUX: "🐧",
        }
        return emojis.get(self.platform, "📱")
    
    @property
    def protocol_display_name(self) -> str:
        """Get protocol display name"""
        names = {
            VPNProtocol.WIREGUARD: "WireGuard",
            VPNProtocol.VLESS_REALITY: "VLESS Reality",
            VPNProtocol.XRAY: "Xray",
            VPNProtocol.SINGBOX: "sing-box",
            VPNProtocol.OUTLINE: "Outline",
        }
        return names.get(self.protocol, self.protocol.value)
    
    @property
    def recommended_app(self) -> str:
        """Get recommended app for platform"""
        if self.platform in [DevicePlatform.ANDROID, DevicePlatform.IOS, DevicePlatform.ANDROID_TV]:
            return "Happ"
        elif self.platform == DevicePlatform.WINDOWS:
            return "Hiddify"
        else:
            return "Official Client"
