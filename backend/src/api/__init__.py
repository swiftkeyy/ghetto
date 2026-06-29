"""
API Router - Main routing configuration
"""

from fastapi import APIRouter

from src.api.routes import (
    users,
    subscriptions,
    servers,
    devices,
    payments,
    admin,
    stats,
)

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    tags=["Subscriptions"]
)

api_router.include_router(
    servers.router,
    prefix="/servers",
    tags=["Servers"]
)

api_router.include_router(
    devices.router,
    prefix="/devices",
    tags=["Devices"]
)

api_router.include_router(
    payments.router,
    prefix="/payments",
    tags=["Payments"]
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)

api_router.include_router(
    stats.router,
    prefix="/stats",
    tags=["Statistics"]
)
