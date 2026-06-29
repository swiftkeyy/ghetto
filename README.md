# 🚀 GHETTO VPN

**Premium Commercial VPN Telegram Bot - Production Ready**

A world-class VPN service built with Telegram Bot API, featuring multi-protocol support, premium UI/UX, and enterprise-grade admin panel.

## ✨ Key Features

### User Experience
- 🎨 **Dark Elite Luxury Design** - Glassmorphism with neon accents
- 📱 **Multi-Platform Support** - Android, iOS, Android TV, Windows
- ⚡ **One-Click Connection** - Seamless device setup with QR codes
- 🌍 **Smart Server Selection** - Real-time ping, load monitoring
- 💎 **Flexible Subscriptions** - 1/3/6/12 months + Lifetime plans
- 🎁 **Referral System** - Earn rewards for inviting friends
- 📊 **Usage Statistics** - Track bandwidth and connections
- 🌐 **Multi-language** - English + Russian

### VPN Protocols
- WireGuard
- VLESS Reality
- Xray
- sing-box
- Outline

### Admin Panel (CRM)
- 📈 Real-time Dashboard with metrics
- 👥 User Management (search, CRUD, blocking)
- 💳 Subscription Management
- 🖥️ Server Management & Monitoring
- 🎟️ Promo Code System
- 📧 Segmented Broadcasting
- 💰 Financial Analytics
- 🔍 Audit Logs

### Technical Stack
- **Backend**: Python 3.12, FastAPI, aiogram 3.x
- **Database**: PostgreSQL + Redis
- **Architecture**: Clean Architecture + DDD
- **Admin Panel**: Next.js 15, TypeScript, shadcn/ui
- **DevOps**: Docker, Nginx, GitHub Actions
- **Monitoring**: Prometheus, Grafana, Sentry

## 🏗️ Project Structure

```
ghetto-vpn/
├── backend/                 # Python backend
│   ├── src/
│   │   ├── bot/            # Telegram bot (aiogram)
│   │   ├── api/            # FastAPI REST API
│   │   ├── core/           # Core business logic
│   │   ├── domain/         # Domain models & entities
│   │   ├── infrastructure/ # Database, external services
│   │   └── vpn/            # VPN protocols implementation
│   ├── alembic/            # Database migrations
│   └── tests/              # Unit & integration tests
├── admin/                   # Next.js admin panel
│   ├── src/
│   │   ├── app/            # App Router
│   │   ├── components/     # React components
│   │   ├── lib/            # Utilities
│   │   └── styles/         # CSS/Tailwind
├── docker/                  # Docker configurations
├── nginx/                   # Nginx configs
├── monitoring/             # Prometheus, Grafana
└── docs/                   # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis 7

### Installation

1. Clone repository:
```bash
git clone https://github.com/yourusername/ghetto-vpn.git
cd ghetto-vpn
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Start with Docker:
```bash
docker-compose up -d
```

4. Run migrations:
```bash
docker-compose exec backend alembic upgrade head
```

5. Create admin user:
```bash
docker-compose exec backend python -m src.cli create-admin
```

### Access Points
- **Telegram Bot**: @YourBotUsername
- **Admin Panel**: https://admin.yourdomain.com
- **API Docs**: https://api.yourdomain.com/docs
- **Monitoring**: https://monitoring.yourdomain.com

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration](docs/configuration.md)
- [API Reference](docs/api.md)
- [Admin Panel Guide](docs/admin-panel.md)
- [VPN Setup](docs/vpn-setup.md)
- [Deployment](docs/deployment.md)

## 🔒 Security

- Rate limiting & anti-flood protection
- JWT authentication with refresh tokens
- Argon2 password hashing
- SQL injection prevention
- XSS protection
- Secrets management with environment variables
- Automated security updates

## 📊 Monitoring

- Prometheus metrics collection
- Grafana dashboards
- Loki log aggregation
- Sentry error tracking
- Real-time alerts

## 🛠️ Development

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.bot

# Admin panel development
cd admin
npm install
npm run dev
```

## 📝 License

Proprietary - All Rights Reserved

## 💬 Support

For support and inquiries: support@ghettovpn.com

---

**Built with ❤️ for the next generation of VPN services**
