"""
Application configuration and settings
"""

from typing import List, Optional
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # ============================================================================
    # CORE SETTINGS
    # ============================================================================
    ENVIRONMENT: str = Field(default="production")
    DEBUG: bool = Field(default=False)
    SECRET_KEY: str = Field(...)
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    
    # ============================================================================
    # TELEGRAM BOT
    # ============================================================================
    BOT_TOKEN: str = Field(...)
    BOT_WEBHOOK_URL: Optional[str] = Field(default=None)
    BOT_WEBHOOK_SECRET: Optional[str] = Field(default=None)
    ADMIN_USER_IDS: str = Field(default="")
    
    @field_validator("ADMIN_USER_IDS")
    @classmethod
    def parse_admin_ids(cls, v: str) -> List[int]:
        if not v:
            return []
        return [int(id.strip()) for id in v.split(",") if id.strip()]
    
    # ============================================================================
    # DATABASE
    # ============================================================================
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="ghettovpn")
    POSTGRES_USER: str = Field(default="ghettovpn")
    POSTGRES_PASSWORD: str = Field(...)
    DATABASE_URL: str = Field(default="")
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=40)
    
    @field_validator("DATABASE_URL")
    @classmethod
    def build_database_url(cls, v: str, values) -> str:
        if v:
            return v
        data = values.data
        return (
            f"postgresql+asyncpg://{data['POSTGRES_USER']}:{data['POSTGRES_PASSWORD']}"
            f"@{data['POSTGRES_HOST']}:{data['POSTGRES_PORT']}/{data['POSTGRES_DB']}"
        )
    
    # ============================================================================
    # REDIS
    # ============================================================================
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_URL: str = Field(default="")
    
    @field_validator("REDIS_URL")
    @classmethod
    def build_redis_url(cls, v: str, values) -> str:
        if v:
            return v
        data = values.data
        password = f":{data['REDIS_PASSWORD']}@" if data.get('REDIS_PASSWORD') else ""
        return f"redis://{password}{data['REDIS_HOST']}:{data['REDIS_PORT']}/{data['REDIS_DB']}"
    
    # ============================================================================
    # JWT & SECURITY
    # ============================================================================
    JWT_SECRET_KEY: str = Field(...)
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)
    
    PASSWORD_HASH_TIME_COST: int = Field(default=2)
    PASSWORD_HASH_MEMORY_COST: int = Field(default=65536)
    PASSWORD_HASH_PARALLELISM: int = Field(default=4)
    
    RATE_LIMIT_REQUESTS: int = Field(default=30)
    RATE_LIMIT_WINDOW: int = Field(default=60)
    
    # ============================================================================
    # VPN CONFIGURATION
    # ============================================================================
    WIREGUARD_ENABLED: bool = Field(default=True)
    WIREGUARD_PORT: int = Field(default=51820)
    WIREGUARD_INTERFACE: str = Field(default="wg0")
    WIREGUARD_DNS: str = Field(default="1.1.1.1,1.0.0.1")
    
    VLESS_ENABLED: bool = Field(default=True)
    VLESS_PORT: int = Field(default=443)
    VLESS_FLOW: str = Field(default="xtls-rprx-vision")
    
    XRAY_ENABLED: bool = Field(default=True)
    XRAY_API_PORT: int = Field(default=8080)
    XRAY_CONFIG_PATH: str = Field(default="/etc/xray/config.json")
    
    SINGBOX_ENABLED: bool = Field(default=True)
    SINGBOX_API_PORT: int = Field(default=9090)
    SINGBOX_CONFIG_PATH: str = Field(default="/etc/sing-box/config.json")
    
    OUTLINE_ENABLED: bool = Field(default=True)
    OUTLINE_API_URL: Optional[str] = Field(default=None)
    OUTLINE_API_KEY: Optional[str] = Field(default=None)
    
    # ============================================================================
    # PAYMENT PROVIDERS
    # ============================================================================
    STRIPE_ENABLED: bool = Field(default=True)
    STRIPE_PUBLIC_KEY: Optional[str] = Field(default=None)
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None)
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None)
    
    CRYPTO_ENABLED: bool = Field(default=True)
    CRYPTO_API_KEY: Optional[str] = Field(default=None)
    CRYPTO_SHOP_ID: Optional[str] = Field(default=None)
    
    YOOKASSA_ENABLED: bool = Field(default=True)
    YOOKASSA_SHOP_ID: Optional[str] = Field(default=None)
    YOOKASSA_SECRET_KEY: Optional[str] = Field(default=None)
    
    TELEGRAM_PAYMENT_TOKEN: Optional[str] = Field(default=None)
    
    # ============================================================================
    # SUBSCRIPTION PLANS (USD)
    # ============================================================================
    PLAN_1_MONTH_PRICE: float = Field(default=9.99)
    PLAN_3_MONTHS_PRICE: float = Field(default=24.99)
    PLAN_6_MONTHS_PRICE: float = Field(default=44.99)
    PLAN_12_MONTHS_PRICE: float = Field(default=79.99)
    PLAN_LIFETIME_PRICE: float = Field(default=299.99)
    
    TRIAL_ENABLED: bool = Field(default=True)
    TRIAL_DAYS: int = Field(default=3)
    TRIAL_BANDWIDTH_GB: float = Field(default=10.0)
    
    # ============================================================================
    # REFERRAL SYSTEM
    # ============================================================================
    REFERRAL_ENABLED: bool = Field(default=True)
    REFERRAL_REWARD_DAYS: int = Field(default=7)
    REFERRAL_DISCOUNT_PERCENT: int = Field(default=10)
    REFERRAL_MIN_PAYOUT: float = Field(default=10.00)
    
    # ============================================================================
    # EMAIL
    # ============================================================================
    EMAIL_ENABLED: bool = Field(default=False)
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    EMAIL_FROM: str = Field(default="noreply@ghettovpn.com")
    
    # ============================================================================
    # MONITORING & LOGGING
    # ============================================================================
    SENTRY_ENABLED: bool = Field(default=True)
    SENTRY_DSN: Optional[str] = Field(default=None)
    SENTRY_ENVIRONMENT: str = Field(default="production")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1)
    
    PROMETHEUS_ENABLED: bool = Field(default=True)
    PROMETHEUS_PORT: int = Field(default=9091)
    
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    
    # ============================================================================
    # ADMIN PANEL
    # ============================================================================
    ADMIN_PANEL_URL: str = Field(default="https://admin.yourdomain.com")
    ADMIN_SESSION_SECRET: str = Field(...)
    NEXTAUTH_URL: Optional[str] = Field(default=None)
    NEXTAUTH_SECRET: Optional[str] = Field(default=None)
    
    # ============================================================================
    # SERVER LOCATIONS
    # ============================================================================
    DEFAULT_SERVERS: str = Field(default="")
    
    # ============================================================================
    # CDN & ASSETS
    # ============================================================================
    CDN_ENABLED: bool = Field(default=False)
    CDN_URL: Optional[str] = Field(default=None)
    ASSETS_PATH: str = Field(default="/app/assets")
    
    # ============================================================================
    # BACKUP
    # ============================================================================
    BACKUP_ENABLED: bool = Field(default=True)
    BACKUP_SCHEDULE: str = Field(default="0 2 * * *")
    BACKUP_RETENTION_DAYS: int = Field(default=30)
    BACKUP_S3_BUCKET: Optional[str] = Field(default=None)
    BACKUP_S3_REGION: str = Field(default="us-east-1")
    BACKUP_S3_ACCESS_KEY: Optional[str] = Field(default=None)
    BACKUP_S3_SECRET_KEY: Optional[str] = Field(default=None)
    
    # ============================================================================
    # FEATURE FLAGS
    # ============================================================================
    FEATURE_WEB_APP: bool = Field(default=True)
    FEATURE_ANDROID_TV: bool = Field(default=True)
    FEATURE_MULTI_DEVICE: bool = Field(default=True)
    FEATURE_BANDWIDTH_TRACKING: bool = Field(default=True)
    FEATURE_ANALYTICS: bool = Field(default=True)
    FEATURE_PROMO_CODES: bool = Field(default=True)
    FEATURE_REWARDS: bool = Field(default=True)
    
    # ============================================================================
    # LOCALIZATION
    # ============================================================================
    DEFAULT_LANGUAGE: str = Field(default="en")
    SUPPORTED_LANGUAGES: str = Field(default="en,ru")
    TIMEZONE: str = Field(default="UTC")
    
    @field_validator("SUPPORTED_LANGUAGES")
    @classmethod
    def parse_languages(cls, v: str) -> List[str]:
        return [lang.strip() for lang in v.split(",") if lang.strip()]
    
    # ============================================================================
    # ADVANCED
    # ============================================================================
    MAX_DEVICES_PER_USER: int = Field(default=5)
    MAX_SIMULTANEOUS_CONNECTIONS: int = Field(default=3)
    BANDWIDTH_CHECK_INTERVAL: int = Field(default=300)
    SERVER_HEALTH_CHECK_INTERVAL: int = Field(default=60)
    CONFIG_CACHE_TTL: int = Field(default=3600)
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def admin_ids(self) -> List[int]:
        if isinstance(self.ADMIN_USER_IDS, list):
            return self.ADMIN_USER_IDS
        return []


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
