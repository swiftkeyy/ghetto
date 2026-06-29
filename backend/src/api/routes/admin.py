"""
Admin API Router
"""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.domain.models import (
    User,
    Server,
    Subscription,
    Payment,
    Device,
    Connection,
    PromoCode,
    PromoCodeType,
    UserStatus,
)
from src.api.dependencies.auth import get_current_admin_user
from src.core.config import settings

router = APIRouter()


# ============================================================================
# DASHBOARD STATS
# ============================================================================

@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get dashboard overview statistics
    """
    # Users stats
    query = select(User)
    result = await db.execute(query)
    all_users = result.scalars().all()
    
    total_users = len(all_users)
    premium_users = sum(1 for u in all_users if u.is_premium)
    active_users = sum(1 for u in all_users if u.status == UserStatus.ACTIVE)
    blocked_users = sum(1 for u in all_users if u.status == UserStatus.BLOCKED)
    
    # Today's new users
    today = datetime.utcnow().date()
    today_users = sum(1 for u in all_users if u.created_at.date() == today)
    
    # Servers stats
    query = select(Server)
    result = await db.execute(query)
    servers = result.scalars().all()
    
    total_servers = len(servers)
    online_servers = sum(1 for s in servers if s.status.value == "online")
    
    # Payments stats
    query = select(Payment)
    result = await db.execute(query)
    payments = result.scalars().all()
    
    total_revenue = sum(p.amount for p in payments if p.status.value == "completed")
    today_revenue = sum(
        p.amount for p in payments
        if p.status.value == "completed" and p.completed_at and p.completed_at.date() == today
    )
    
    # This month revenue
    this_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_revenue = sum(
        p.amount for p in payments
        if p.status.value == "completed" and p.completed_at and p.completed_at >= this_month
    )
    
    # Active connections
    query = select(Connection).where(Connection.is_active == True)
    result = await db.execute(query)
    active_connections = len(result.scalars().all())
    
    # Bandwidth usage
    total_bandwidth = sum(u.total_bandwidth_used for u in all_users)
    
    return {
        "users": {
            "total": total_users,
            "premium": premium_users,
            "active": active_users,
            "blocked": blocked_users,
            "today_new": today_users,
        },
        "servers": {
            "total": total_servers,
            "online": online_servers,
            "offline": total_servers - online_servers,
        },
        "revenue": {
            "total": total_revenue,
            "today": today_revenue,
            "this_month": this_month_revenue,
            "currency": "USD",
        },
        "connections": {
            "active": active_connections,
        },
        "bandwidth": {
            "total_gb": total_bandwidth,
        }
    }


# ============================================================================
# USER MANAGEMENT
# ============================================================================

@router.get("/users/search")
async def search_users(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Search users by username, telegram_id, or name
    """
    search_query = select(User).where(
        or_(
            User.username.ilike(f"%{query}%"),
            User.first_name.ilike(f"%{query}%"),
            User.telegram_id == int(query) if query.isdigit() else False
        )
    ).limit(limit)
    
    result = await db.execute(search_query)
    users = result.scalars().all()
    
    return {
        "results": [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "username": u.username,
                "first_name": u.first_name,
                "is_premium": u.is_premium,
                "status": u.status.value,
                "created_at": u.created_at,
            }
            for u in users
        ],
        "total": len(users)
    }


@router.post("/users/{user_id}/grant-subscription")
async def grant_subscription(
    user_id: int,
    days: int = Query(..., ge=1, le=36500),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Grant subscription days to user (Admin only)
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate new subscription end date
    start_date = datetime.utcnow()
    if user.subscription_end and user.subscription_end > start_date:
        start_date = user.subscription_end
    
    end_date = start_date + timedelta(days=days)
    
    # Create subscription
    from src.domain.models import SubscriptionPlan, SubscriptionStatus
    
    subscription = Subscription(
        user_id=user.id,
        plan=SubscriptionPlan.MONTH_1,  # Generic plan for manual grants
        status=SubscriptionStatus.ACTIVE,
        start_date=start_date,
        end_date=end_date,
        price=0.0,
        currency="USD",
    )
    
    db.add(subscription)
    
    # Update user
    user.is_premium = True
    user.subscription_end = end_date
    
    await db.commit()
    
    return {
        "message": f"Granted {days} days to user",
        "user_id": user_id,
        "subscription_end": end_date,
    }


# ============================================================================
# PROMO CODE MANAGEMENT
# ============================================================================

@router.get("/promo-codes")
async def get_promo_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get all promo codes (Admin only)
    """
    query = select(PromoCode)
    
    if active_only:
        query = query.where(PromoCode.is_active == True)
    
    query = query.offset(skip).limit(limit).order_by(PromoCode.created_at.desc())
    result = await db.execute(query)
    promo_codes = result.scalars().all()
    
    return {
        "items": [
            {
                "id": p.id,
                "code": p.code,
                "type": p.type.value,
                "value": p.value,
                "max_uses": p.max_uses,
                "current_uses": p.current_uses,
                "is_active": p.is_active,
                "valid_from": p.valid_from,
                "valid_until": p.valid_until,
                "created_at": p.created_at,
            }
            for p in promo_codes
        ],
        "total": len(promo_codes)
    }


@router.post("/promo-codes")
async def create_promo_code(
    code: str = Query(..., min_length=3, max_length=50),
    type: PromoCodeType = Query(...),
    value: float = Query(..., gt=0),
    max_uses: Optional[int] = Query(None, gt=0),
    valid_days: Optional[int] = Query(None, gt=0),
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Create new promo code (Admin only)
    """
    # Check if code already exists
    query = select(PromoCode).where(PromoCode.code == code.upper())
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Promo code already exists"
        )
    
    # Calculate valid_until
    valid_until = None
    if valid_days:
        valid_until = datetime.utcnow() + timedelta(days=valid_days)
    
    # Create promo code
    promo = PromoCode(
        code=code.upper(),
        description=description,
        type=type,
        value=value,
        max_uses=max_uses,
        valid_until=valid_until,
        is_active=True,
        created_by=admin.id,
    )
    
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    
    return {
        "message": "Promo code created successfully",
        "promo_code": {
            "id": promo.id,
            "code": promo.code,
            "type": promo.type.value,
            "value": promo.value,
        }
    }


@router.patch("/promo-codes/{promo_id}")
async def update_promo_code(
    promo_id: int,
    is_active: Optional[bool] = None,
    max_uses: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Update promo code (Admin only)
    """
    query = select(PromoCode).where(PromoCode.id == promo_id)
    result = await db.execute(query)
    promo = result.scalar_one_or_none()
    
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found"
        )
    
    if is_active is not None:
        promo.is_active = is_active
    
    if max_uses is not None:
        promo.max_uses = max_uses
    
    await db.commit()
    
    return {
        "message": "Promo code updated successfully",
        "promo_code": {
            "id": promo.id,
            "code": promo.code,
            "is_active": promo.is_active,
        }
    }


@router.delete("/promo-codes/{promo_id}")
async def delete_promo_code(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Delete promo code (Admin only)
    """
    query = select(PromoCode).where(PromoCode.id == promo_id)
    result = await db.execute(query)
    promo = result.scalar_one_or_none()
    
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promo code not found"
        )
    
    await db.delete(promo)
    await db.commit()
    
    return {"message": "Promo code deleted successfully"}


# ============================================================================
# BROADCAST
# ============================================================================

@router.post("/broadcast")
async def broadcast_message(
    message: str = Query(..., min_length=1),
    target: str = Query("all", regex="^(all|premium|free|active)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Send broadcast message to users (Admin only)
    """
    # Get target users
    query = select(User)
    
    if target == "premium":
        query = query.where(User.is_premium == True)
    elif target == "free":
        query = query.where(User.is_premium == False)
    elif target == "active":
        query = query.where(User.status == UserStatus.ACTIVE)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # TODO: Send message to all users via bot
    # This should be done asynchronously using Celery task
    
    return {
        "message": "Broadcast scheduled",
        "target": target,
        "total_recipients": len(users),
    }


# ============================================================================
# SYSTEM SETTINGS
# ============================================================================

@router.get("/settings")
async def get_system_settings(
    admin: User = Depends(get_current_admin_user),
):
    """
    Get system settings (Admin only)
    """
    return {
        "app": {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        },
        "features": {
            "trial_enabled": settings.TRIAL_ENABLED,
            "trial_days": settings.TRIAL_DAYS,
            "referral_enabled": settings.REFERRAL_ENABLED,
            "web_app": settings.FEATURE_WEB_APP,
            "android_tv": settings.FEATURE_ANDROID_TV,
        },
        "limits": {
            "max_devices_per_user": settings.MAX_DEVICES_PER_USER,
            "max_simultaneous_connections": settings.MAX_SIMULTANEOUS_CONNECTIONS,
        },
        "pricing": {
            "1_month": settings.PLAN_1_MONTH_PRICE,
            "3_months": settings.PLAN_3_MONTHS_PRICE,
            "6_months": settings.PLAN_6_MONTHS_PRICE,
            "12_months": settings.PLAN_12_MONTHS_PRICE,
            "lifetime": settings.PLAN_LIFETIME_PRICE,
            "currency": "USD",
        },
        "vpn": {
            "wireguard_enabled": settings.WIREGUARD_ENABLED,
            "vless_enabled": settings.VLESS_ENABLED,
            "xray_enabled": settings.XRAY_ENABLED,
        },
        "payments": {
            "stripe_enabled": settings.STRIPE_ENABLED,
            "crypto_enabled": settings.CRYPTO_ENABLED,
            "yookassa_enabled": settings.YOOKASSA_ENABLED,
        }
    }


@router.get("/logs")
async def get_system_logs(
    lines: int = Query(100, ge=1, le=1000),
    level: str = Query("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get system logs (Admin only)
    """
    # TODO: Read logs from file or logging system
    return {
        "message": "Log retrieval not implemented yet",
        "lines": lines,
        "level": level,
    }
