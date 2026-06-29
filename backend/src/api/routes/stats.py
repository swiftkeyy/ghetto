"""
Statistics API Router
"""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.domain.models import (
    User,
    Connection,
    Payment,
    Subscription,
    Server,
    Device,
)
from src.api.dependencies.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


# ============================================================================
# USER STATISTICS
# ============================================================================

@router.get("/my")
async def get_my_statistics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Get current user's statistics
    """
    # Get connections
    query = select(Connection).where(Connection.user_id == user.id)
    result = await db.execute(query)
    connections = result.scalars().all()
    
    total_connections = len(connections)
    active_connections = sum(1 for c in connections if c.is_active)
    
    # Calculate total bandwidth
    total_bytes_sent = sum(c.bytes_sent for c in connections)
    total_bytes_received = sum(c.bytes_received for c in connections)
    total_bytes = total_bytes_sent + total_bytes_received
    total_gb = total_bytes / (1024 ** 3)
    
    # Calculate average session duration
    durations = [c.duration_seconds for c in connections if c.duration_seconds]
    avg_duration_seconds = sum(durations) / len(durations) if durations else 0
    
    # Get devices
    query = select(Device).where(Device.user_id == user.id)
    result = await db.execute(query)
    devices = result.scalars().all()
    
    # Last 7 days activity
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_connections = [c for c in connections if c.connected_at >= seven_days_ago]
    
    # Daily stats for last 7 days
    daily_stats = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_connections = [
            c for c in connections
            if day_start <= c.connected_at < day_end
        ]
        
        day_bytes = sum(c.bytes_sent + c.bytes_received for c in day_connections)
        day_gb = day_bytes / (1024 ** 3)
        
        daily_stats.append({
            "date": day_start.date().isoformat(),
            "connections": len(day_connections),
            "bandwidth_gb": round(day_gb, 2),
        })
    
    daily_stats.reverse()
    
    # Subscription info
    subscription_status = "inactive"
    subscription_days_left = 0
    
    if user.is_premium and user.subscription_end:
        subscription_status = "active"
        subscription_days_left = max(0, (user.subscription_end - datetime.utcnow()).days)
    
    return {
        "overview": {
            "total_bandwidth_gb": round(total_gb, 2),
            "total_connections": total_connections,
            "active_connections": active_connections,
            "total_devices": len(devices),
            "active_devices": sum(1 for d in devices if d.is_active),
            "average_session_minutes": round(avg_duration_seconds / 60, 1),
        },
        "subscription": {
            "status": subscription_status,
            "is_premium": user.is_premium,
            "days_left": subscription_days_left,
            "end_date": user.subscription_end.isoformat() if user.subscription_end else None,
        },
        "recent_activity": {
            "last_7_days": daily_stats,
            "connections_count": len(recent_connections),
        },
        "top_servers": await _get_user_top_servers(user.id, db),
    }


async def _get_user_top_servers(user_id: int, db: AsyncSession) -> List[dict]:
    """Get user's most used servers"""
    query = select(Connection).where(Connection.user_id == user_id)
    result = await db.execute(query)
    connections = result.scalars().all()
    
    # Count connections per server
    server_counts = {}
    for conn in connections:
        server_counts[conn.server_id] = server_counts.get(conn.server_id, 0) + 1
    
    # Get top 5 servers
    top_server_ids = sorted(server_counts.keys(), key=lambda x: server_counts[x], reverse=True)[:5]
    
    top_servers = []
    for server_id in top_server_ids:
        query = select(Server).where(Server.id == server_id)
        result = await db.execute(query)
        server = result.scalar_one_or_none()
        
        if server:
            top_servers.append({
                "id": server.id,
                "name": server.name,
                "country": server.country,
                "city": server.city,
                "connections": server_counts[server_id],
            })
    
    return top_servers


# ============================================================================
# ADMIN STATISTICS
# ============================================================================

@router.get("/overview")
async def get_overview_statistics(
    period: str = Query("30d", regex="^(7d|30d|90d|365d|all)$"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get overview statistics for admin dashboard
    """
    # Calculate date range
    now = datetime.utcnow()
    if period == "7d":
        start_date = now - timedelta(days=7)
    elif period == "30d":
        start_date = now - timedelta(days=30)
    elif period == "90d":
        start_date = now - timedelta(days=90)
    elif period == "365d":
        start_date = now - timedelta(days=365)
    else:
        start_date = None
    
    # Users
    query = select(User)
    result = await db.execute(query)
    all_users = result.scalars().all()
    
    if start_date:
        period_users = [u for u in all_users if u.created_at >= start_date]
    else:
        period_users = all_users
    
    # Payments
    query = select(Payment)
    result = await db.execute(query)
    all_payments = result.scalars().all()
    
    if start_date:
        period_payments = [p for p in all_payments if p.created_at >= start_date]
    else:
        period_payments = all_payments
    
    completed_payments = [p for p in period_payments if p.status.value == "completed"]
    total_revenue = sum(p.amount for p in completed_payments)
    
    # Connections
    query = select(Connection)
    result = await db.execute(query)
    all_connections = result.scalars().all()
    
    if start_date:
        period_connections = [c for c in all_connections if c.connected_at >= start_date]
    else:
        period_connections = all_connections
    
    # Bandwidth
    total_bandwidth_bytes = sum(
        c.bytes_sent + c.bytes_received for c in period_connections
    )
    total_bandwidth_gb = total_bandwidth_bytes / (1024 ** 3)
    
    return {
        "period": period,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": now.isoformat(),
        "users": {
            "total": len(all_users),
            "new_in_period": len(period_users),
            "premium": sum(1 for u in all_users if u.is_premium),
            "active": sum(1 for u in all_users if u.status.value == "active"),
        },
        "revenue": {
            "total": round(total_revenue, 2),
            "transactions": len(completed_payments),
            "average_transaction": round(total_revenue / len(completed_payments), 2) if completed_payments else 0,
            "currency": "USD",
        },
        "connections": {
            "total": len(period_connections),
            "active": sum(1 for c in period_connections if c.is_active),
        },
        "bandwidth": {
            "total_gb": round(total_bandwidth_gb, 2),
            "average_per_user_gb": round(total_bandwidth_gb / len(all_users), 2) if all_users else 0,
        }
    }


@router.get("/growth")
async def get_growth_statistics(
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get growth statistics over time
    """
    query = select(User)
    result = await db.execute(query)
    all_users = result.scalars().all()
    
    query = select(Payment)
    result = await db.execute(query)
    all_payments = result.scalars().all()
    
    # Generate daily stats
    daily_stats = []
    for i in range(days):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # New users on this day
        day_users = [u for u in all_users if day_start <= u.created_at < day_end]
        
        # Payments on this day
        day_payments = [
            p for p in all_payments
            if p.completed_at and day_start <= p.completed_at < day_end and p.status.value == "completed"
        ]
        day_revenue = sum(p.amount for p in day_payments)
        
        daily_stats.append({
            "date": day_start.date().isoformat(),
            "new_users": len(day_users),
            "revenue": round(day_revenue, 2),
            "transactions": len(day_payments),
        })
    
    daily_stats.reverse()
    
    return {
        "period_days": days,
        "daily_stats": daily_stats,
    }


@router.get("/servers")
async def get_server_statistics(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get server statistics
    """
    query = select(Server)
    result = await db.execute(query)
    servers = result.scalars().all()
    
    query = select(Connection)
    result = await db.execute(query)
    connections = result.scalars().all()
    
    server_stats = []
    for server in servers:
        server_connections = [c for c in connections if c.server_id == server.id]
        
        total_bandwidth = sum(
            c.bytes_sent + c.bytes_received for c in server_connections
        )
        total_bandwidth_gb = total_bandwidth / (1024 ** 3)
        
        active_connections = sum(1 for c in server_connections if c.is_active)
        
        server_stats.append({
            "id": server.id,
            "name": server.name,
            "country": server.country,
            "city": server.city,
            "status": server.status.value,
            "protocol": server.protocol.value,
            "total_connections": len(server_connections),
            "active_connections": active_connections,
            "bandwidth_gb": round(total_bandwidth_gb, 2),
            "load_percentage": server.load_percentage,
            "current_users": server.current_users,
        })
    
    # Sort by connections
    server_stats.sort(key=lambda x: x["total_connections"], reverse=True)
    
    return {
        "total_servers": len(servers),
        "servers": server_stats,
    }


@router.get("/referrals")
async def get_referral_statistics(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get referral system statistics
    """
    query = select(User)
    result = await db.execute(query)
    all_users = result.scalars().all()
    
    # Users with referrals
    users_with_referrals = [u for u in all_users if u.referred_by_id is not None]
    
    # Top referrers
    referrer_counts = {}
    for user in users_with_referrals:
        referrer_counts[user.referred_by_id] = referrer_counts.get(user.referred_by_id, 0) + 1
    
    top_referrers = []
    for referrer_id in sorted(referrer_counts.keys(), key=lambda x: referrer_counts[x], reverse=True)[:10]:
        query = select(User).where(User.id == referrer_id)
        result = await db.execute(query)
        referrer = result.scalar_one_or_none()
        
        if referrer:
            referrals = [u for u in all_users if u.referred_by_id == referrer_id]
            premium_referrals = sum(1 for r in referrals if r.is_premium)
            
            top_referrers.append({
                "id": referrer.id,
                "telegram_id": referrer.telegram_id,
                "username": referrer.username,
                "first_name": referrer.first_name,
                "total_referrals": referrer_counts[referrer_id],
                "premium_referrals": premium_referrals,
            })
    
    return {
        "total_referred_users": len(users_with_referrals),
        "conversion_rate": round(len(users_with_referrals) / len(all_users) * 100, 2) if all_users else 0,
        "top_referrers": top_referrers,
    }


@router.get("/devices")
async def get_device_statistics(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get device platform statistics
    """
    query = select(Device)
    result = await db.execute(query)
    devices = result.scalars().all()
    
    # Group by platform
    platform_counts = {}
    for device in devices:
        platform = device.platform.value
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
    
    platform_stats = [
        {
            "platform": platform,
            "count": count,
            "percentage": round(count / len(devices) * 100, 2) if devices else 0,
        }
        for platform, count in platform_counts.items()
    ]
    
    platform_stats.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total_devices": len(devices),
        "active_devices": sum(1 for d in devices if d.is_active),
        "by_platform": platform_stats,
    }


@router.get("/retention")
async def get_retention_statistics(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get user retention statistics
    """
    query = select(User)
    result = await db.execute(query)
    all_users = result.scalars().all()
    
    now = datetime.utcnow()
    
    # Active in last 24h, 7d, 30d
    active_24h = sum(
        1 for u in all_users
        if u.last_activity and (now - u.last_activity).total_seconds() < 86400
    )
    
    active_7d = sum(
        1 for u in all_users
        if u.last_activity and (now - u.last_activity).days < 7
    )
    
    active_30d = sum(
        1 for u in all_users
        if u.last_activity and (now - u.last_activity).days < 30
    )
    
    total_users = len(all_users)
    
    return {
        "total_users": total_users,
        "retention": {
            "24h": {
                "count": active_24h,
                "percentage": round(active_24h / total_users * 100, 2) if total_users else 0,
            },
            "7d": {
                "count": active_7d,
                "percentage": round(active_7d / total_users * 100, 2) if total_users else 0,
            },
            "30d": {
                "count": active_30d,
                "percentage": round(active_30d / total_users * 100, 2) if total_users else 0,
            }
        }
    }
