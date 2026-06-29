# GHETTO VPN - Database Architecture

## 🗄️ PostgreSQL Schema Design

### Overview
- **Database**: PostgreSQL 16+
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Caching**: Redis 7+

---

## Core Tables

### 1. users
Primary user table for Telegram users.

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'en',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_blocked BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    
    -- Referral
    referred_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    referral_code VARCHAR(20) UNIQUE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT check_telegram_id_positive CHECK (telegram_id > 0)
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_referral_code ON users(referral_code);
CREATE INDEX idx_users_referred_by ON users(referred_by_id);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
```

---

### 2. subscriptions
User subscription plans and status.

```sql
CREATE TYPE subscription_plan_type AS ENUM (
    'trial',
    'monthly',
    'quarterly',
    'semi_annual',
    'annual',
    'lifetime'
);

CREATE TYPE subscription_status AS ENUM (
    'active',
    'expired',
    'cancelled',
    'suspended',
    'pending'
);

CREATE TABLE subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Plan details
    plan_type subscription_plan_type NOT NULL,
    status subscription_status NOT NULL DEFAULT 'pending',
    
    -- Duration
    started_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_lifetime BOOLEAN DEFAULT FALSE,
    
    -- Limits
    traffic_limit_gb INTEGER, -- NULL = unlimited
    traffic_used_gb DECIMAL(12, 3) DEFAULT 0,
    device_limit INTEGER DEFAULT 5,
    
    -- Auto-renewal
    auto_renew BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_traffic_positive CHECK (traffic_used_gb >= 0),
    CONSTRAINT check_device_limit_positive CHECK (device_limit > 0)
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_expires_at ON subscriptions(expires_at) WHERE status = 'active';
CREATE UNIQUE INDEX idx_subscriptions_active_user ON subscriptions(user_id) 
    WHERE status = 'active';
```

---

### 3. servers
VPN servers with multi-protocol support.

```sql
CREATE TYPE server_status AS ENUM ('online', 'offline', 'maintenance');

CREATE TABLE servers (
    id SERIAL PRIMARY KEY,
    
    -- Location
    name VARCHAR(255) NOT NULL,
    country_code VARCHAR(2) NOT NULL, -- ISO 3166-1 alpha-2
    country_name VARCHAR(255) NOT NULL,
    city VARCHAR(255),
    region VARCHAR(255),
    
    -- Server details
    host VARCHAR(255) NOT NULL,
    public_ip INET NOT NULL,
    management_port INTEGER DEFAULT 22,
    
    -- Protocol support flags
    supports_wireguard BOOLEAN DEFAULT TRUE,
    supports_vless BOOLEAN DEFAULT TRUE,
    supports_xray BOOLEAN DEFAULT TRUE,
    supports_singbox BOOLEAN DEFAULT TRUE,
    supports_outline BOOLEAN DEFAULT FALSE,
    
    -- WireGuard configuration
    wireguard_port INTEGER DEFAULT 51820,
    wireguard_public_key TEXT,
    wireguard_endpoint VARCHAR(255),
    wireguard_allowed_ips TEXT DEFAULT '0.0.0.0/0, ::/0',
    
    -- VLESS Reality configuration
    vless_port INTEGER DEFAULT 443,
    vless_uuid UUID,
    vless_reality_public_key TEXT,
    vless_reality_short_id TEXT,
    vless_reality_server_name TEXT,
    
    -- Xray configuration
    xray_port INTEGER DEFAULT 443,
    xray_config JSONB,
    
    -- sing-box configuration
    singbox_port INTEGER DEFAULT 443,
    singbox_config JSONB,
    
    -- Outline configuration
    outline_api_url TEXT,
    outline_cert_sha256 TEXT,
    
    -- Status & monitoring
    status server_status DEFAULT 'online',
    is_active BOOLEAN DEFAULT TRUE,
    is_recommended BOOLEAN DEFAULT FALSE,
    
    -- Performance metrics
    load_percentage INTEGER DEFAULT 0, -- 0-100
    ping_ms INTEGER,
    bandwidth_mbps INTEGER,
    max_users INTEGER DEFAULT 1000,
    current_users INTEGER DEFAULT 0,
    
    -- Features
    supports_p2p BOOLEAN DEFAULT TRUE,
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_torrenting BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_health_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT check_load_percentage CHECK (load_percentage >= 0 AND load_percentage <= 100),
    CONSTRAINT check_current_users_positive CHECK (current_users >= 0),
    CONSTRAINT check_max_users_positive CHECK (max_users > 0)
);

CREATE INDEX idx_servers_country_code ON servers(country_code);
CREATE INDEX idx_servers_status ON servers(status);
CREATE INDEX idx_servers_is_active ON servers(is_active);
CREATE INDEX idx_servers_is_recommended ON servers(is_recommended);
CREATE INDEX idx_servers_load_percentage ON servers(load_percentage);
CREATE INDEX idx_servers_country_active ON servers(country_code, is_active);
```

---

### 4. devices
User devices and VPN configurations.

```sql
CREATE TYPE device_platform AS ENUM (
    'android',
    'ios',
    'android_tv',
    'windows',
    'macos',
    'linux'
);

CREATE TYPE vpn_protocol AS ENUM (
    'wireguard',
    'vless_reality',
    'xray',
    'singbox',
    'outline'
);

CREATE TABLE devices (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    server_id INTEGER REFERENCES servers(id) ON DELETE SET NULL,
    
    -- Device info
    name VARCHAR(255) NOT NULL, -- User-defined name
    platform device_platform NOT NULL,
    protocol vpn_protocol NOT NULL,
    
    -- VPN configuration
    config_data TEXT NOT NULL, -- Full config (base64 encoded)
    config_url TEXT, -- Import URL (for one-tap)
    qr_code_path TEXT, -- Path to QR code image
    
    -- WireGuard specific
    wireguard_public_key TEXT,
    wireguard_private_key TEXT, -- Encrypted
    wireguard_address INET, -- Client IP in VPN network
    
    -- VLESS/Xray specific
    vless_uuid UUID,
    
    -- sing-box specific
    singbox_uuid UUID,
    
    -- Outline specific
    outline_access_key TEXT,
    
    -- Status & statistics
    is_active BOOLEAN DEFAULT TRUE,
    last_connection_at TIMESTAMP WITH TIME ZONE,
    last_disconnect_at TIMESTAMP WITH TIME ZONE,
    total_connections INTEGER DEFAULT 0,
    
    -- Traffic statistics
    traffic_upload_gb DECIMAL(12, 3) DEFAULT 0,
    traffic_download_gb DECIMAL(12, 3) DEFAULT 0,
    traffic_total_gb DECIMAL(12, 3) GENERATED ALWAYS AS (traffic_upload_gb + traffic_download_gb) STORED,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT check_traffic_positive CHECK (
        traffic_upload_gb >= 0 AND traffic_download_gb >= 0
    )
);

CREATE INDEX idx_devices_user_id ON devices(user_id);
CREATE INDEX idx_devices_server_id ON devices(server_id);
CREATE INDEX idx_devices_is_active ON devices(is_active);
CREATE INDEX idx_devices_platform ON devices(platform);
CREATE INDEX idx_devices_protocol ON devices(protocol);
CREATE UNIQUE INDEX idx_devices_wireguard_pubkey ON devices(wireguard_public_key) 
    WHERE wireguard_public_key IS NOT NULL;
```

---

### 5. payments
Payment transactions and history.

```sql
CREATE TYPE payment_provider AS ENUM (
    'yookassa',
    'stripe',
    'crypto_usdt',
    'crypto_btc',
    'crypto_eth'
);

CREATE TYPE payment_status AS ENUM (
    'pending',
    'processing',
    'succeeded',
    'failed',
    'refunded',
    'cancelled'
);

CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id BIGINT REFERENCES subscriptions(id) ON DELETE SET NULL,
    
    -- Payment details
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'RUB', -- ISO 4217
    provider payment_provider NOT NULL,
    provider_payment_id VARCHAR(255) UNIQUE,
    provider_order_id VARCHAR(255),
    
    -- Plan info
    plan_type subscription_plan_type NOT NULL,
    duration_days INTEGER,
    
    -- Discount
    promo_code_id INTEGER REFERENCES promo_codes(id) ON DELETE SET NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    final_amount DECIMAL(10, 2) NOT NULL,
    
    -- Status
    status payment_status NOT NULL DEFAULT 'pending',
    
    -- Additional data
    payment_method VARCHAR(100), -- e.g., 'bank_card', 'sbp', 'wallet'
    payment_url TEXT, -- URL for user to complete payment
    webhook_data JSONB, -- Raw webhook data
    metadata JSONB, -- Custom metadata
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- Payment link expiration
    succeeded_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    refunded_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT check_amounts_positive CHECK (
        amount > 0 AND final_amount > 0 AND discount_amount >= 0
    ),
    CONSTRAINT check_final_amount CHECK (final_amount <= amount)
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_subscription_id ON payments(subscription_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_provider ON payments(provider);
CREATE INDEX idx_payments_provider_payment_id ON payments(provider_payment_id);
CREATE INDEX idx_payments_created_at ON payments(created_at DESC);
CREATE INDEX idx_payments_pending ON payments(status, created_at) 
    WHERE status = 'pending';
```

---

### 6. promo_codes
Promotional discount codes.

```sql
CREATE TYPE promo_discount_type AS ENUM (
    'percentage',      -- e.g., 20% off
    'fixed_amount',    -- e.g., $10 off
    'free_days'        -- e.g., +7 days
);

CREATE TABLE promo_codes (
    id SERIAL PRIMARY KEY,
    
    -- Code details
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    
    -- Discount configuration
    discount_type promo_discount_type NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    
    -- Usage limitations
    max_uses INTEGER, -- NULL = unlimited
    current_uses INTEGER DEFAULT 0,
    max_uses_per_user INTEGER DEFAULT 1,
    min_purchase_amount DECIMAL(10, 2),
    
    -- Plan restrictions
    applicable_plans subscription_plan_type[], -- NULL = all plans
    
    -- User restrictions
    user_whitelist BIGINT[], -- Specific user IDs (NULL = all users)
    
    -- Validity period
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Creator
    created_by_admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT check_discount_value_positive CHECK (discount_value > 0),
    CONSTRAINT check_percentage_range CHECK (
        discount_type != 'percentage' OR (discount_value > 0 AND discount_value <= 100)
    ),
    CONSTRAINT check_uses CHECK (current_uses <= COALESCE(max_uses, current_uses))
);

CREATE UNIQUE INDEX idx_promo_codes_code ON promo_codes(UPPER(code));
CREATE INDEX idx_promo_codes_is_active ON promo_codes(is_active);
CREATE INDEX idx_promo_codes_valid_period ON promo_codes(valid_from, valid_until);
```

---

### 7. referrals
Referral system tracking.

```sql
CREATE TYPE referral_reward_type AS ENUM (
    'free_days',
    'discount_percentage',
    'cashback'
);

CREATE TYPE referral_reward_status AS ENUM (
    'pending',
    'earned',
    'applied',
    'expired'
);

CREATE TABLE referrals (
    id BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    referred_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Reward configuration
    reward_type referral_reward_type NOT NULL DEFAULT 'free_days',
    reward_value DECIMAL(10, 2) NOT NULL,
    reward_status referral_reward_status DEFAULT 'pending',
    
    -- Tracking
    referred_registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    referred_subscribed BOOLEAN DEFAULT FALSE,
    referred_subscription_id BIGINT REFERENCES subscriptions(id),
    referred_payment_id BIGINT REFERENCES payments(id),
    
    -- Reward details
    reward_earned_at TIMESTAMP WITH TIME ZONE,
    reward_applied_at TIMESTAMP WITH TIME ZONE,
    reward_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT check_different_users CHECK (referrer_id != referred_id),
    UNIQUE(referrer_id, referred_id)
);

CREATE INDEX idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX idx_referrals_referred ON referrals(referred_id);
CREATE INDEX idx_referrals_status ON referrals(reward_status);
CREATE INDEX idx_referrals_pending ON referrals(referrer_id, reward_status) 
    WHERE reward_status = 'pending';
```

---

### 8. connections
Connection logs and session tracking.

```sql
CREATE TYPE connection_status AS ENUM (
    'active',
    'disconnected',
    'failed'
);

CREATE TABLE connections (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id BIGINT REFERENCES devices(id) ON DELETE SET NULL,
    server_id INTEGER REFERENCES servers(id) ON DELETE SET NULL,
    
    -- Connection details
    status connection_status DEFAULT 'active',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (COALESCE(ended_at, NOW()) - started_at))::INTEGER
    ) STORED,
    
    -- Traffic
    bytes_sent BIGINT DEFAULT 0,
    bytes_received BIGINT DEFAULT 0,
    bytes_total BIGINT GENERATED ALWAYS AS (bytes_sent + bytes_received) STORED,
    
    -- Connection metadata
    client_ip INET,
    server_ip INET,
    protocol vpn_protocol,
    
    -- Disconnect info
    disconnect_reason VARCHAR(100), -- 'user', 'timeout', 'error', 'maintenance'
    error_message TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT check_traffic_positive CHECK (bytes_sent >= 0 AND bytes_received >= 0)
);

-- Partitioning by month for performance
CREATE INDEX idx_connections_user_id ON connections(user_id, started_at DESC);
CREATE INDEX idx_connections_device_id ON connections(device_id);
CREATE INDEX idx_connections_server_id ON connections(server_id);
CREATE INDEX idx_connections_started_at ON connections(started_at DESC);
CREATE INDEX idx_connections_active ON connections(user_id, status) 
    WHERE status = 'active';
```

---

### 9. admins
Admin users with role-based access.

```sql
CREATE TYPE admin_role AS ENUM (
    'super_admin',
    'admin',
    'moderator',
    'support',
    'viewer'
);

CREATE TABLE admins (
    id SERIAL PRIMARY KEY,
    
    -- Identity
    telegram_id BIGINT UNIQUE,
    username VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    
    -- Authentication
    password_hash TEXT NOT NULL, -- Argon2
    
    -- Role & permissions
    role admin_role NOT NULL DEFAULT 'admin',
    permissions JSONB DEFAULT '[]', -- Custom permissions array
    
    -- Two-factor authentication
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT check_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE UNIQUE INDEX idx_admins_email ON admins(LOWER(email));
CREATE UNIQUE INDEX idx_admins_telegram_id ON admins(telegram_id) 
    WHERE telegram_id IS NOT NULL;
CREATE INDEX idx_admins_is_active ON admins(is_active);
```

---

### 10. audit_logs
System audit trail for compliance.

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    admin_id INTEGER REFERENCES admins(id) ON DELETE SET NULL,
    
    -- Action details
    action VARCHAR(100) NOT NULL, -- e.g., 'user.blocked', 'server.created'
    entity_type VARCHAR(50) NOT NULL, -- 'user', 'server', 'payment', etc.
    entity_id BIGINT,
    
    -- Changes
    old_data JSONB,
    new_data JSONB,
    
    -- Request context
    ip_address INET,
    user_agent TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_admin_id ON audit_logs(admin_id, created_at DESC);
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

---

### 11. notifications
User notification queue.

```sql
CREATE TYPE notification_type AS ENUM (
    'subscription_expiring',
    'subscription_expired',
    'payment_succeeded',
    'payment_failed',
    'new_server',
    'server_maintenance',
    'referral_earned',
    'system_announcement'
);

CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification details
    type notification_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    is_sent BOOLEAN DEFAULT FALSE,
    send_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Scheduled send time
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unsent ON notifications(is_sent, send_at) 
    WHERE is_sent = FALSE;
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read) 
    WHERE is_read = FALSE;
```

---

### 12. system_settings
Global system configuration.

```sql
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE, -- Can be exposed via API
    
    -- Metadata
    updated_by_admin_id INTEGER REFERENCES admins(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_system_settings_key ON system_settings(key);
```

---

## Redis Schema (Caching Layer)

### Key Patterns

```
# User sessions
session:user:{user_id}                          -> User session data (JSON, TTL: 24h)
session:user:{user_id}:last_activity           -> Timestamp (TTL: 24h)

# Rate limiting
ratelimit:user:{telegram_id}:{action}          -> Counter (TTL: 60s)
ratelimit:ip:{ip_address}                      -> Counter (TTL: 60s)
ratelimit:payment:{user_id}                    -> Counter (TTL: 1h)

# Active connections
connection:user:{user_id}:active               -> Active connection info (JSON)
connection:server:{server_id}:users            -> Set of active user_ids

# Cache
cache:servers:active                           -> List of active servers (JSON, TTL: 5min)
cache:server:{server_id}:stats                 -> Server stats (JSON, TTL: 1min)
cache:user:{user_id}:subscription              -> User subscription (JSON, TTL: 10min)
cache:user:{user_id}:devices                   -> User devices list (JSON, TTL: 5min)
cache:promo:{code}                             -> Promo code data (JSON, TTL: 1h)

# Locks (distributed locking)
lock:payment:{user_id}                         -> Lock for payment processing (TTL: 30s)
lock:device:create:{user_id}                   -> Lock for device creation (TTL: 10s)

# Queues (Celery)
celery:*                                       -> Task queues

# Temporary data
temp:qr:{device_id}                            -> QR code data (TTL: 15min)
temp:payment:{payment_id}                      -> Payment session (TTL: 30min)
```

---

## Relationships Diagram

```
┌──────────┐
│  users   │
└─────┬────┘
      │
      ├──── subscriptions (1:N)
      ├──── devices (1:N)
      ├──── payments (1:N)
      ├──── connections (1:N)
      ├──── notifications (1:N)
      ├──── referrals (as referrer) (1:N)
      └──── referrals (as referred) (1:N)

┌──────────┐
│ servers  │
└─────┬────┘
      │
      ├──── devices (1:N)
      └──── connections (1:N)

┌──────────────┐
│ promo_codes  │
└─────┬────────┘
      │
      └──── payments (1:N)

┌──────────┐
│  admins  │
└─────┬────┘
      │
      ├──── promo_codes (1:N)
      └──── audit_logs (1:N)
```

---

## Performance Optimizations

1. **Indexing Strategy**
   - All foreign keys indexed
   - Composite indexes for common queries
   - Partial indexes for filtered queries
   - Generated columns for computed values

2. **Partitioning**
   - `connections` table partitioned by month
   - Archive old data to cold storage

3. **Caching**
   - Redis for hot data
   - Cache invalidation on writes
   - TTL-based expiration

4. **Connection Pooling**
   - SQLAlchemy async pool
   - PgBouncer for connection pooling

5. **Query Optimization**
   - Eager loading for relationships
   - Pagination for large result sets
   - EXPLAIN ANALYZE for slow queries

---

## Backup Strategy

- **Full backup**: Daily at 3:00 UTC
- **Incremental backup**: Every 6 hours
- **WAL archiving**: Continuous
- **Retention**: 30 days
- **Testing**: Weekly restore verification

---

**Database design complete. Ready for SQLAlchemy model implementation.**
