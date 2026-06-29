"""
GHETTO VPN - Core Configuration Module
Handles all application settings using Pydantic BaseSettings
"""

from typing import List, Optional
from functools import lru_cache

from pydantic import Field, field_validator, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ============================================
    # Application Settings
    # ============================================
    app_name: str = Field(default="GHETTO VPN", description="Application name")
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of worker processes")
    
    # ============================================
    # Database Settings (PostgreSQL)
    # ============================================
    database_host: str = Field(default="localhost", description="Database host")
    database_port: int = Field(default=5432, description="Database port")
    database_name: str = Field(default="ghetto_vpn", description="Database name")
    database_user: str = Field(default="postgres", description="Database user")
    database_password: str = Field(description="Database password")
    database_pool_size: int = Field(default=20, description="Connection pool size")
    database_max_overflow: int = Field(default=10, description="Max overflow connections")
    
    @property
    def database_url(self) -> str:
        """Generate async PostgreSQL connection URL"""
        return (
            f"postgresql+asyncpg://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )
    
    @property
    def database_url_sync(self) -> str:
        """Generate sync PostgreSQL connection URL (for Alembic)"""
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )
    
    # ============================================
    # Redis Settings
    # ============================================
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_pool_size: int = Field(default=10, description="Redis connection pool size")
    
    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # ============================================
    # Telegram Bot Settings
    # ============================================
    telegram_bot_token: str = Field(description="Telegram bot token from @BotFather")
    telegram_webhook_url: Optional[str] = Field(default=None, description="Webhook URL for bot")
    telegram_webhook_path: str = Field(default="/webhook", description="Webhook path")
    telegram_admin_ids: str = Field(default="", description="Comma-separated admin Telegram IDs")
    
    @property
    def telegram_admin_ids_list(self) -> List[int]:
        """Parse admin IDs from comma-separated string"""
        if not self.telegram_admin_ids:
            return []
        return [int(id.strip()) for id in self.telegram_admin_ids.split(",") if id.strip()]
    
    # ============================================
    # Security Settings
    # ============================================
    secret_key: str = Field(description="Application secret key")
    jwt_secret_key: str = Field(description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration (minutes)")
    refresh_token_expire_days: int = Field(default=30, description="Refresh token expiration (days)")
    
    # Password Hashing (Argon2)
    argon2_time_cost: int = Field(default=2, description="Argon2 time cost")
    argon2_memory_cost: int = Field(default=65536, description="Argon2 memory cost")
    argon2_parallelism: int = Field(default=4, description="Argon2 parallelism")
    
    # ============================================
    # CORS Settings
    # ============================================
    cors_origins: str = Field(default="*", description="Comma-separated allowed origins")
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    # ============================================
    # Rate Limiting
    # ============================================
    rate_limit_per_minute: int = Field(default=60, description="Max requests per minute")
    rate_limit_per_hour: int = Field(default=1000, description="Max requests per hour")
    
    # ============================================
    # Payment Providers
    # ============================================
    # YooKassa
    yookassa_shop_id: Optional[str] = Field(default=None, description="YooKassa shop ID")
    yookassa_secret_key: Optional[str] = Field(default=None, description="YooKassa secret key")
    yookassa_webhook_secret: Optional[str] = Field(default=None, description="YooKassa webhook secret")
    
    # Stripe
    stripe_public_key: Optional[str] = Field(default=None, description="Stripe public key")
    stripe_secret_key: Optional[str] = Field(default=None, description="Stripe secret key")
    stripe_webhook_secret: Optional[str] = Field(default=None, description="Stripe webhook secret")
    
    # Crypto
    crypto_usdt_address: Optional[str] = Field(default=None, description="USDT wallet address")
    crypto_btc_address: Optional[str] = Field(default=None, description="BTC wallet address")
    crypto_eth_address: Optional[str] = Field(default=None, description="ETH wallet address")
    
    # ============================================
    # VPN Protocol Settings
    # ============================================
    wireguard_enabled: bool = Field(default=True, description="Enable WireGuard")
    wireguard_subnet: str = Field(default="10.8.0.0/24", description="WireGuard subnet")
    wireguard_dns: str = Field(default="1.1.1.1,8.8.8.8", description="WireGuard DNS servers")
    
    vless_enabled: bool = Field(default=True, description="Enable VLESS Reality")
    xray_enabled: bool = Field(default=True, description="Enable Xray")
    singbox_enabled: bool = Field(default=True, description="Enable sing-box")
    outline_enabled: bool = Field(default=False, description="Enable Outline VPN")
    
    # ============================================
    # Subscription Plans
    # ============================================
    plan_trial_days: int = Field(default=3, description="Trial plan duration (days)")
    plan_monthly_days: int = Field(default=30, description="Monthly plan duration")
    plan_quarterly_days: int = Field(default=90, description="Quarterly plan duration")
    plan_semi_annual_days: int = Field(default=180, description="Semi-annual plan duration")
    plan_annual_days: int = Field(default=365, description="Annual plan duration")
    
    # Prices (RUB)
    price_monthly: int = Field(default=299, description="Monthly plan price")
    price_quarterly: int = Field(default=799, description="Quarterly plan price")
    price_semi_annual: int = Field(default=1499, description="Semi-annual plan price")
    price_annual: int = Field(default=2499, description="Annual plan price")
    price_lifetime: int = Field(default=9999, description="Lifetime plan price")
    
    # ============================================
    # Referral System
    # ============================================
    referral_reward_days: int = Field(default=7, description="Referral reward (free days)")
    referral_reward_enabled: bool = Field(default=True, description="Enable referral rewards")
    
    # ============================================
    # File Storage
    # ============================================
    upload_dir: str = Field(default="./uploads", description="Upload directory")
    qr_code_dir: str = Field(default="./uploads/qr_codes", description="QR code directory")
    max_upload_size: int = Field(default=5242880, description="Max upload size (5MB)")
    
    # ============================================
    # Celery (Background Tasks)
    # ============================================
    celery_broker_url: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", description="Celery result backend")
    celery_task_serializer: str = Field(default="json", description="Task serializer")
    celery_result_serializer: str = Field(default="json", description="Result serializer")
    celery_timezone: str = Field(default="UTC", description="Celery timezone")
    
    # ============================================
    # Monitoring
    # ============================================
    # Sentry
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    sentry_environment: str = Field(default="development", description="Sentry environment")
    sentry_traces_sample_rate: float = Field(default=0.1, description="Sentry traces sample rate")
    
    # Prometheus
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus port")
    
    # ============================================
    # Logging
    # ============================================
    log_file: str = Field(default="./logs/app.log", description="Log file path")
    log_max_bytes: int = Field(default=10485760, description="Max log file size (10MB)")
    log_backup_count: int = Field(default=5, description="Number of log backups")
    log_format: str = Field(default="json", description="Log format: json or text")
    
    # ============================================
    # Backup
    # ============================================
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")
    backup_dir: str = Field(default="./backups", description="Backup directory")
    backup_retention_days: int = Field(default=30, description="Backup retention period")
    
    # ============================================
    # Email (Optional)
    # ============================================
    smtp_host: Optional[str] = Field(default=None, description="SMTP host")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP user")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from: str = Field(default="noreply@ghettovpn.com", description="SMTP from address")
    
    # ============================================
    # Admin Panel
    # ============================================
    admin_panel_url: str = Field(default="https://admin.ghettovpn.com", description="Admin panel URL")
    admin_session_lifetime: int = Field(default=86400, description="Admin session lifetime (seconds)")
    
    # ============================================
    # Maintenance Mode
    # ============================================
    maintenance_mode: bool = Field(default=False, description="Enable maintenance mode")
    maintenance_message: str = Field(
        default="We are currently performing maintenance. Please check back soon.",
        description="Maintenance message"
    )
    
    # ============================================
    # Feature Flags
    # ============================================
    feature_crypto_payments: bool = Field(default=False, description="Enable crypto payments")
    feature_referral_system: bool = Field(default=True, description="Enable referral system")
    feature_promo_codes: bool = Field(default=True, description="Enable promo codes")
    feature_trial_subscription: bool = Field(default=True, description="Enable trial subscriptions")
    
    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v_upper
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to create a singleton.
    """
    return Settings()


# Global settings instance
settings = get_settings()
