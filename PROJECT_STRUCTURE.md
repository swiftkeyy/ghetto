# GHETTO VPN - Complete Project Structure

## 🏗️ Architecture Overview

```
ghetto-vpn/
├── backend/                          # Python Backend (FastAPI + aiogram 3.x)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application entry
│   │   ├── bot_main.py               # Telegram bot entry
│   │   │
│   │   ├── core/                     # Core configurations & utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Settings (Pydantic BaseSettings)
│   │   │   ├── security.py           # JWT, Argon2 hashing, encryption
│   │   │   ├── dependencies.py       # FastAPI dependencies
│   │   │   └── logging.py            # Structured logging setup
│   │   │
│   │   ├── db/                       # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # SQLAlchemy Base & imports
│   │   │   ├── session.py            # DB session management
│   │   │   └── redis.py              # Redis connection pool
│   │   │
│   │   ├── models/                   # SQLAlchemy ORM Models
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # User model
│   │   │   ├── subscription.py       # Subscription & plans
│   │   │   ├── server.py             # VPN servers
│   │   │   ├── device.py             # User devices & configs
│   │   │   ├── payment.py            # Payment transactions
│   │   │   ├── promo_code.py         # Promo codes
│   │   │   ├── referral.py           # Referral system
│   │   │   ├── connection.py         # Connection logs
│   │   │   ├── admin.py              # Admin users
│   │   │   ├── notification.py       # Notifications queue
│   │   │   └── audit_log.py          # Audit trail
│   │   │
│   │   ├── schemas/                  # Pydantic Schemas (DTO)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── subscription.py
│   │   │   ├── server.py
│   │   │   ├── device.py
│   │   │   ├── payment.py
│   │   │   ├── promo_code.py
│   │   │   ├── referral.py
│   │   │   ├── stats.py
│   │   │   └── common.py             # Shared schemas
│   │   │
│   │   ├── api/                      # FastAPI REST API
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── api.py            # Main API router
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── auth.py       # Admin authentication
│   │   │           ├── users.py      # User management CRUD
│   │   │           ├── servers.py    # Server management
│   │   │           ├── subscriptions.py
│   │   │           ├── payments.py   # Payment webhooks
│   │   │           ├── devices.py    # Device config generation
│   │   │           ├── promo_codes.py
│   │   │           ├── referrals.py
│   │   │           ├── stats.py      # Analytics & statistics
│   │   │           ├── broadcasts.py # Mass notifications
│   │   │           └── health.py     # Health check endpoint
│   │   │
│   │   ├── bot/                      # Telegram Bot (aiogram 3.x)
│   │   │   ├── __init__.py
│   │   │   ├── bot.py                # Bot instance initialization
│   │   │   ├── dispatcher.py         # Dispatcher & router setup
│   │   │   │
│   │   │   ├── handlers/             # Message & callback handlers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── start.py          # /start - onboarding flow
│   │   │   │   ├── menu.py           # Main menu navigation
│   │   │   │   ├── servers.py        # Server selection & filtering
│   │   │   │   ├── devices.py        # Device connection flow
│   │   │   │   ├── subscription.py   # Plans & payment flow
│   │   │   │   ├── profile.py        # User profile management
│   │   │   │   ├── stats.py          # User statistics
│   │   │   │   ├── referrals.py      # Referral system & rewards
│   │   │   │   ├── settings.py       # User settings
│   │   │   │   ├── support.py        # Support & FAQ
│   │   │   │   └── admin.py          # Admin bot commands
│   │   │   │
│   │   │   ├── keyboards/            # Inline keyboards (NO ReplyKeyboard!)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── menu.py           # Main menu keyboards
│   │   │   │   ├── servers.py        # Server selection keyboards
│   │   │   │   ├── devices.py        # Device platform selection
│   │   │   │   ├── subscription.py   # Subscription plans
│   │   │   │   ├── profile.py        # Profile actions
│   │   │   │   ├── referrals.py      # Referral actions
│   │   │   │   └── factory.py        # Keyboard builder utilities
│   │   │   │
│   │   │   ├── middlewares/          # Bot middlewares
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py           # User registration & validation
│   │   │   │   ├── throttling.py     # Anti-flood rate limiting
│   │   │   │   ├── logging.py        # Request/response logging
│   │   │   │   └── i18n.py           # Internationalization
│   │   │   │
│   │   │   ├── states/               # FSM States (for inline flows)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── device.py         # Device setup states
│   │   │   │   └── payment.py        # Payment flow states
│   │   │   │
│   │   │   └── utils/                # Bot utilities
│   │   │       ├── __init__.py
│   │   │       ├── messages.py       # Message templates (i18n)
│   │   │       ├── formatting.py     # Text formatting helpers
│   │   │       ├── qr_generator.py   # QR code generation
│   │   │       └── validators.py     # Input validation
│   │   │
│   │   ├── vpn/                      # VPN Management Core
│   │   │   ├── __init__.py
│   │   │   ├── manager.py            # Main VPN manager orchestrator
│   │   │   ├── config_generator.py   # Config generation facade
│   │   │   │
│   │   │   └── protocols/            # Protocol implementations
│   │   │       ├── __init__.py
│   │   │       ├── base.py           # Abstract base protocol interface
│   │   │       ├── wireguard.py      # WireGuard implementation
│   │   │       ├── vless_reality.py  # VLESS Reality implementation
│   │   │       ├── xray.py           # Xray-core implementation
│   │   │       ├── singbox.py        # sing-box implementation
│   │   │       └── outline.py        # Outline VPN implementation
│   │   │
│   │   ├── services/                 # Business Logic Layer
│   │   │   ├── __init__.py
│   │   │   ├── user_service.py       # User CRUD & logic
│   │   │   ├── subscription_service.py
│   │   │   ├── server_service.py
│   │   │   ├── device_service.py
│   │   │   ├── payment_service.py
│   │   │   ├── promo_code_service.py
│   │   │   ├── referral_service.py
│   │   │   ├── stats_service.py
│   │   │   ├── notification_service.py
│   │   │   └── broadcast_service.py
│   │   │
│   │   ├── tasks/                    # Background Tasks (Celery)
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py         # Celery application
│   │   │   ├── subscription_tasks.py # Subscription expiry checks
│   │   │   ├── server_tasks.py       # Server health monitoring
│   │   │   ├── notification_tasks.py # Scheduled notifications
│   │   │   └── stats_tasks.py        # Statistics aggregation
│   │   │
│   │   └── utils/                    # Shared Utilities
│   │       ├── __init__.py
│   │       ├── date.py               # Date/time helpers
│   │       ├── validators.py         # Common validators
│   │       └── crypto.py             # Encryption utilities
│   │
│   ├── alembic/                      # Database Migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── tests/                        # Test Suite
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── test_api/
│   │   ├── test_bot/
│   │   ├── test_services/
│   │   └── test_vpn/
│   │
│   ├── locales/                      # i18n translations
│   │   ├── en/
│   │   │   └── messages.json
│   │   └── ru/
│   │       └── messages.json
│   │
│   ├── requirements.txt              # Python dependencies
│   ├── requirements-dev.txt          # Development dependencies
│   ├── pyproject.toml                # Project metadata
│   ├── .env.example                  # Environment variables template
│   ├── alembic.ini                   # Alembic configuration
│   └── pytest.ini                    # Pytest configuration
│
├── admin-panel/                      # Next.js 15 Admin Dashboard
│   ├── src/
│   │   ├── app/                      # App Router (Next.js 15)
│   │   │   ├── layout.tsx            # Root layout
│   │   │   ├── globals.css           # Global styles
│   │   │   │
│   │   │   ├── (auth)/               # Auth group
│   │   │   │   ├── layout.tsx        # Auth layout
│   │   │   │   └── login/
│   │   │   │       └── page.tsx      # Login page
│   │   │   │
│   │   │   └── (dashboard)/          # Dashboard group
│   │   │       ├── layout.tsx        # Dashboard layout
│   │   │       ├── page.tsx          # Main dashboard
│   │   │       ├── users/
│   │   │       │   └── page.tsx      # Users management
│   │   │       ├── subscriptions/
│   │   │       │   └── page.tsx      # Subscriptions
│   │   │       ├── servers/
│   │   │       │   └── page.tsx      # Server monitoring
│   │   │       ├── promo-codes/
│   │   │       │   └── page.tsx      # Promo codes
│   │   │       ├── referrals/
│   │   │       │   └── page.tsx      # Referrals
│   │   │       ├── broadcasts/
│   │   │       │   └── page.tsx      # Mass broadcasts
│   │   │       ├── payments/
│   │   │       │   └── page.tsx      # Financial analytics
│   │   │       ├── logs/
│   │   │       │   └── page.tsx      # Audit logs
│   │   │       └── settings/
│   │   │           └── page.tsx      # System settings
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                   # shadcn/ui components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── table.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── select.tsx
│   │   │   │   └── ...               # More shadcn components
│   │   │   │
│   │   │   ├── dashboard/            # Dashboard-specific
│   │   │   │   ├── stats-card.tsx
│   │   │   │   ├── revenue-chart.tsx
│   │   │   │   ├── user-table.tsx
│   │   │   │   ├── server-monitor.tsx
│   │   │   │   ├── live-map.tsx
│   │   │   │   └── activity-feed.tsx
│   │   │   │
│   │   │   └── layout/               # Layout components
│   │   │       ├── sidebar.tsx
│   │   │       ├── header.tsx
│   │   │       ├── nav.tsx
│   │   │       └── theme-toggle.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                # API client (fetch wrapper)
│   │   │   ├── utils.ts              # Utility functions (cn, etc.)
│   │   │   └── auth.ts               # Auth utilities
│   │   │
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── use-api.ts
│   │   │   ├── use-stats.ts
│   │   │   └── use-websocket.ts
│   │   │
│   │   └── types/                    # TypeScript types
│   │       ├── index.ts
│   │       ├── user.ts
│   │       ├── server.ts
│   │       ├── subscription.ts
│   │       └── stats.ts
│   │
│   ├── public/
│   │   ├── logo.svg
│   │   └── favicon.ico
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── postcss.config.js
│   └── .env.local.example
│
├── docker/                           # Docker configurations
│   ├── backend.Dockerfile            # Backend production image
│   ├── admin.Dockerfile              # Admin panel image
│   ├── nginx.Dockerfile              # Nginx reverse proxy
│   └── celery.Dockerfile             # Celery worker image
│
├── nginx/                            # Nginx configurations
│   ├── nginx.conf                    # Main config
│   ├── api.conf                      # API upstream
│   ├── admin.conf                    # Admin panel upstream
│   └── ssl/                          # SSL certificates directory
│
├── scripts/                          # Utility scripts
│   ├── backup.sh                     # Database backup
│   ├── restore.sh                    # Database restore
│   ├── deploy.sh                     # Deployment script
│   └── init_admin.py                 # Create first admin user
│
├── docs/                             # Documentation
│   ├── README.md
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── API.md                        # API documentation
│   ├── VPN_SETUP.md                  # VPN protocols setup
│   ├── ADMIN_GUIDE.md                # Admin panel guide
│   └── DEVELOPMENT.md                # Development setup
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    # CI pipeline
│       └── deploy.yml                # CD pipeline
│
├── docker-compose.yml                # Local development
├── docker-compose.prod.yml           # Production deployment
├── .gitignore
├── README.md                         # Main readme
└── LICENSE
```

## 🛠️ Technology Stack

### Backend
- **Python 3.12+**
- **FastAPI** - Modern async REST API framework
- **aiogram 3.x** - Async Telegram Bot framework
- **SQLAlchemy 2.0** - SQL ORM with async support
- **Alembic** - Database migrations
- **PostgreSQL 16** - Primary database
- **Redis 7+** - Caching, sessions, rate limiting
- **Celery** - Distributed task queue
- **Pydantic v2** - Data validation

### Admin Panel
- **Next.js 15** (App Router)
- **React 19**
- **TypeScript 5.3+**
- **Tailwind CSS 4**
- **shadcn/ui** - Premium UI components
- **Recharts** - Data visualization
- **TanStack Query v5** - Data fetching & caching

### VPN Protocols
- **WireGuard** - Modern, fast VPN protocol
- **VLESS Reality** - Anti-censorship protocol
- **Xray-core** - Advanced proxy platform
- **sing-box** - Universal proxy platform
- **Outline VPN** - Easy-to-use VPN (optional)

### DevOps & Infrastructure
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy & load balancer
- **Certbot** - Automated SSL certificates
- **GitHub Actions** - CI/CD automation
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **Loki** - Log aggregation
- **Sentry** - Error tracking & monitoring

### Payment Providers
- **ЮKassa (YooMoney)** - Russian payment gateway
- **Stripe** - International payments
- **Cryptocurrency** - USDT, BTC, ETH

### Security & Performance
- **Argon2** - Password hashing
- **JWT** - Token-based authentication
- **Redis Rate Limiting** - DDoS protection
- **HTTPS/TLS 1.3** - Encrypted connections
- **WAF Ready** - Web Application Firewall compatible

## ✨ Key Features

### User Features
✅ Premium dark themed Telegram bot (inline-only)
✅ Multi-protocol VPN support (WireGuard, VLESS, etc.)
✅ One-tap device connection (4 platforms)
✅ Automated config generation with QR codes
✅ Real-time server selection & monitoring
✅ Subscription management (5 tiers)
✅ Traffic & connection statistics
✅ Referral system with rewards
✅ Multi-language support (EN, RU)

### Admin Features
✅ Premium dark themed web dashboard
✅ Real-time analytics & metrics
✅ User management (CRUD, blocking, search)
✅ Server monitoring & health checks
✅ Subscription & payment management
✅ Promo code system
✅ Mass broadcast system
✅ Audit log & security monitoring
✅ Financial analytics
✅ System settings management

### Technical Features
✅ Clean Architecture (DDD + SOLID)
✅ 100% type-safe (Pydantic + TypeScript)
✅ Async/await everywhere
✅ Database connection pooling
✅ Redis caching layer
✅ Background job processing
✅ Automated testing suite
✅ Database migrations
✅ Automated backups
✅ Production-ready deployment

## 🎨 Design System

### Color Palette (Dark Elite Luxury)
- **Background**: `#0A0A0A` (deep black), `#111111` (graphite)
- **Surface**: `#1A1A1A` (elevated dark)
- **Primary**: `#00FF9F` (neon green)
- **Secondary**: `#00CC7A` (muted green)
- **Text**: `#FFFFFF` (primary), `#E0E0E0` (secondary), `#AAAAAA` (tertiary)
- **Success**: `#00FF9F`
- **Error**: `#FF3B5C`
- **Warning**: `#FFB800`

### Typography
- **Primary Font**: Inter (system fallback)
- **Accent Font**: Satoshi (or SF Pro)
- **Sizes**: 12px, 14px, 16px, 18px, 24px, 32px

### UI Principles
- Glassmorphism effects (blur + transparency)
- Micro-interactions & smooth animations
- Consistent spacing (4px, 8px, 12px, 16px, 24px, 32px)
- Depth through shadows & blur
- Neon accents on active states
- NO ReplyKeyboard - InlineKeyboard ONLY

## 📊 Performance Targets
- API response time: < 100ms (p95)
- Bot response time: < 200ms (p95)
- Admin panel load time: < 1s
- Database queries: < 50ms (p95)
- VPN config generation: < 500ms
- Uptime: 99.9%

## 🔒 Security Measures
- Rate limiting (per user, per IP)
- Anti-flood middleware
- JWT with refresh tokens
- Argon2 password hashing
- Input validation & sanitization
- SQL injection prevention (ORM)
- XSS protection
- CSRF tokens
- Secrets management (environment variables)
- Audit logging
- Two-factor authentication (admin)

---

**This is a production-ready, enterprise-grade VPN SaaS platform.**
