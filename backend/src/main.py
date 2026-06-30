"""
Main FastAPI application
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.core.config import settings
from src.infrastructure.database import init_db, close_db
from src.infrastructure.redis import redis_manager
from src.api import api_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sentry integration
if settings.SENTRY_ENABLED and settings.SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events"""
    
    # Startup
    logger.info("🚀 Starting GHETTO VPN application...")
    
    try:
        # Initialize database
        logger.info("📦 Initializing database...")
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize Redis
        logger.info("📦 Connecting to Redis...")
        await redis_manager.connect()
        logger.info("✅ Redis connected")
        
        # Start bot (if webhook not used)
        if True settings.BOT_WEBHOOK_URL:
            logger.info("🤖 Starting Telegram bot in polling mode...")
            from src.bot.main import start_bot
            import asyncio
            asyncio.create_task(start_bot())
        
        logger.info("✅ Application started successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    
    try:
        await redis_manager.disconnect()
        await close_db()
        logger.info("✅ Application shutdown complete")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="GHETTO VPN API",
    description="Premium VPN Service - REST API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [settings.ADMIN_PANEL_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Prometheus metrics
if settings.PROMETHEUS_ENABLED:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "GHETTO VPN",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs" if settings.DEBUG else None
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    try:
        # Check Redis
        redis_ok = await redis_manager.ping()
        
        return {
            "status": "healthy",
            "redis": "connected" if redis_ok else "disconnected",
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# ============================================================================
# TELEGRAM WEBHOOK
# ============================================================================

if settings.BOT_WEBHOOK_URL:
    from aiogram import Bot, Dispatcher
    from aiogram.types import Update
    
    @app.post("/webhook/{secret}")
    async def telegram_webhook(secret: str, update: dict):
        """Handle Telegram webhook"""
        
        if secret != settings.BOT_WEBHOOK_SECRET:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Invalid webhook secret"}
            )
        
        try:
            from src.bot.main import dp, bot
            
            telegram_update = Update(**update)
            await dp.feed_update(bot=bot, update=telegram_update)
            
            return {"status": "ok"}
            
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": str(e)}
            )


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Railway provides PORT environment variable
    port = int(os.getenv("PORT", settings.API_PORT))
    
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
