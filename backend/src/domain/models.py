"""
Database models for GHETTO VPN
Clean Architecture - Domain Layer
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    String, Integer, BigInteger, Boolean, DateTime, Float, Text, JSON,
    ForeignKey, Enum, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# ============================================================================
# ENUMS
# ============================================================================

class UserStatus(str, PyEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class SubscriptionStatus(str, PyEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


class SubscriptionPlan(str, PyEnum):
    MONTH_1 = "1_month"
    MONTHS_3 = "3_months"
    MONTHS_6 = "6_months"
    MONTHS_12 = "12_months"
    LIFETIME = "lifetime"
    TRIAL = "trial"


class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentProvider(str, PyEnum):
    STRIPE = "stripe"
    CRYPTO = "crypto"
    YOOKASSA = "yookassa"
    TELEGRAM = "telegram"
    MANUAL = "manual"


class VPNProtocol(str, PyEnum):
    WIREGUARD = "wireguard"
    VLESS = "vless"
    VMESS = "vmess"
    SHADOWSOCKS = "shadowsocks"
    TROJAN = "trojan"
    HYSTERIA = "hysteria"


class ServerStatus(str, PyEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    OVERLOADED = "overloaded"


class DevicePlatform(str, PyEnum):
    ANDROID = "android"
    IOS = "ios"
    ANDROID_TV = "android_tv"
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class PromoCodeType(str, PyEnum):
    DISCOUNT_PERCENT = "discount_percent"
    DISCOUNT_AMOUNT = "discount_amount"
    FREE_DAYS = "free_days"
    FREE_TRIAL = "free_trial"


# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    
    # Status & Security
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Subscription
    subscription_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Trial
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Referral
    referral_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Statistics
    total_bandwidth_used: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # GB
    total_connections: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    subscriptions: Mapped[List["Subscription"]] = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    connections: Mapped[List["Connection"]] = relationship("Connection", back_populates="user", cascade="all, delete-orphan")
    referrals: Mapped[List["User"]] = relationship("User", backref="referrer", remote_side=[id])
    rewards: Mapped[List["Reward"]] = relationship("Reward", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_users_status", "status"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


# ============================================================================
# SUBSCRIPTION MODEL
# ============================================================================

class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    
    # Dates
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Pricing
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Auto-renewal
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    payment_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("payments.id"), nullable=True)
    promo_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    payment: Mapped[Optional["Payment"]] = relationship("Payment", back_populates="subscription")
    
    __table_args__ = (
        Index("idx_subscriptions_user_status", "user_id", "status"),
        Index("idx_end_date", "end_date"),
    )

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan}, status={self.status})>"


# ============================================================================
# PAYMENT MODEL
# ============================================================================

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Payment details
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    provider: Mapped[PaymentProvider] = mapped_column(Enum(PaymentProvider), nullable=False)
    
    # External IDs
    external_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    invoice_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="payment", uselist=False)
    
    __table_args__ = (
        Index("idx_payments_user_status", "user_id", "status"),
        Index("idx_external_id", "external_id"),
    )

    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"


# ============================================================================
# SERVER MODEL
# ============================================================================

class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Server info
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)  # US-NY
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Network
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv4/IPv6
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[VPNProtocol] = mapped_column(Enum(VPNProtocol), nullable=False)
    
    # Status
    status: Mapped[ServerStatus] = mapped_column(Enum(ServerStatus), default=ServerStatus.ONLINE, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Performance
    load_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ping_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_users: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    current_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Bandwidth
    bandwidth_limit_mbps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bandwidth_used_gb: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Configuration
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Priority (lower = higher priority)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_check: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    connections: Mapped[List["Connection"]] = relationship("Connection", back_populates="server", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_servers_status", "status"),
        Index("idx_country", "country_code"),
        Index("idx_protocol", "protocol"),
    )

    def __repr__(self):
        return f"<Server(id={self.id}, code={self.code}, country={self.country}, status={self.status})>"


# ============================================================================
# DEVICE MODEL
# ============================================================================

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Device info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[DevicePlatform] = mapped_column(Enum(DevicePlatform), nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    
    # VPN Config
    config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Base64 encoded config
    public_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    private_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Encrypted
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Statistics
    total_bandwidth: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # GB
    last_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_connection: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="devices")
    connections: Mapped[List["Connection"]] = relationship("Connection", back_populates="device", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_user_active", "user_id", "is_active"),
    )

    def __repr__(self):
        return f"<Device(id={self.id}, name={self.name}, platform={self.platform})>"


# ============================================================================
# CONNECTION MODEL
# ============================================================================

class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id: Mapped[int] = mapped_column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    server_id: Mapped[int] = mapped_column(Integer, ForeignKey("servers.id"), nullable=False, index=True)
    
    # Connection info
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Bandwidth
    bytes_sent: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bytes_received: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    
    # Duration
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    disconnected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="connections")
    device: Mapped["Device"] = relationship("Device", back_populates="connections")
    server: Mapped["Server"] = relationship("Server", back_populates="connections")
    
    __table_args__ = (
        Index("idx_user_active", "user_id", "is_active"),
        Index("idx_connected_at", "connected_at"),
    )

    def __repr__(self):
        return f"<Connection(id={self.id}, user_id={self.user_id}, server_id={self.server_id})>"


# ============================================================================
# PROMO CODE MODEL
# ============================================================================

class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Code info
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Type & Value
    type: Mapped[PromoCodeType] = mapped_column(Enum(PromoCodeType), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)  # Percent, Amount, or Days
    
    # Limits
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_uses_per_user: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Validity
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Restrictions
    min_purchase_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    applicable_plans: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    
    # Created by
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_active", "is_active"),
        CheckConstraint("max_uses IS NULL OR max_uses > 0", name="check_max_uses_positive"),
        CheckConstraint("value > 0", name="check_value_positive"),
    )

    def __repr__(self):
        return f"<PromoCode(id={self.id}, code={self.code}, type={self.type})>"


# ============================================================================
# REWARD MODEL
# ============================================================================

class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Reward info
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # referral, promo, bonus
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Value
    reward_type: Mapped[str] = mapped_column(String(50), nullable=False)  # days, discount, money
    reward_value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Status
    is_claimed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Related
    related_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Referred user
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="rewards")
    
    __table_args__ = (
        Index("idx_user_claimed", "user_id", "is_claimed"),
    )

    def __repr__(self):
        return f"<Reward(id={self.id}, user_id={self.user_id}, type={self.type})>"
