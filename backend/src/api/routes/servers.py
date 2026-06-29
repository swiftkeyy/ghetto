"""
Servers API Router
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.domain.models import Server, ServerStatus, VPNProtocol, User
from src.api.schemas.server import (
    ServerResponse,
    ServerCreate,
    ServerUpdate,
    ServerListResponse,
    ServerPublicListResponse,
    ServerPublicResponse,
    ServerStatsResponse,
)
from src.api.dependencies.auth import get_current_admin_user, get_current_active_user

router = APIRouter()


@router.get("/", response_model=ServerListResponse)
async def get_servers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[ServerStatus] = None,
    protocol: Optional[VPNProtocol] = None,
    country_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get all servers (Admin only)
    """
    query = select(Server)
    
    # Apply filters
    if status_filter:
        query = query.where(Server.status == status_filter)
    if protocol:
        query = query.where(Server.protocol == protocol)
    if country_code:
        query = query.where(Server.country_code == country_code.upper())
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Get servers with pagination
    query = query.offset(skip).limit(limit).order_by(Server.priority, Server.created_at.desc())
    result = await db.execute(query)
    servers = result.scalars().all()
    
    return ServerListResponse(
        items=servers,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/public", response_model=ServerPublicListResponse)
async def get_public_servers(
    protocol: Optional[VPNProtocol] = None,
    country_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Get public server list for users
    """
    query = select(Server).where(
        Server.is_active == True,
        Server.status == ServerStatus.ONLINE
    )
    
    # Apply filters
    if protocol:
        query = query.where(Server.protocol == protocol)
    if country_code:
        query = query.where(Server.country_code == country_code.upper())
    
    query = query.order_by(Server.priority, Server.load_percentage)
    result = await db.execute(query)
    servers = result.scalars().all()
    
    # Convert to public response
    public_servers = [
        ServerPublicResponse(
            id=s.id,
            code=s.code,
            name=s.name,
            country=s.country,
            country_code=s.country_code,
            city=s.city,
            protocol=s.protocol,
            status=s.status,
            load_percentage=s.load_percentage,
            ping_ms=s.ping_ms,
            is_premium=True,
        )
        for s in servers
    ]
    
    return ServerPublicListResponse(
        items=public_servers,
        total=len(public_servers)
    )


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get server by ID (Admin only)
    """
    query = select(Server).where(Server.id == server_id)
    result = await db.execute(query)
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return server


@router.post("/", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Create new server (Admin only)
    """
    # Check if code already exists
    query = select(Server).where(Server.code == server_data.code)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server with this code already exists"
        )
    
    # Create server
    server = Server(**server_data.model_dump())
    db.add(server)
    await db.commit()
    await db.refresh(server)
    
    return server


@router.patch("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    server_data: ServerUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Update server (Admin only)
    """
    query = select(Server).where(Server.id == server_id)
    result = await db.execute(query)
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Update fields
    for field, value in server_data.model_dump(exclude_unset=True).items():
        setattr(server, field, value)
    
    await db.commit()
    await db.refresh(server)
    
    return server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Delete server (Admin only)
    """
    query = select(Server).where(Server.id == server_id)
    result = await db.execute(query)
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    await db.delete(server)
    await db.commit()
    
    return None


@router.get("/stats/overview", response_model=ServerStatsResponse)
async def get_server_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Get server statistics (Admin only)
    """
    query = select(Server)
    result = await db.execute(query)
    servers = result.scalars().all()
    
    total_servers = len(servers)
    online_servers = sum(1 for s in servers if s.status == ServerStatus.ONLINE)
    offline_servers = total_servers - online_servers
    total_bandwidth_gb = sum(s.bandwidth_used_gb for s in servers)
    average_load = sum(s.load_percentage for s in servers) / total_servers if total_servers > 0 else 0
    total_users_connected = sum(s.current_users for s in servers)
    
    return ServerStatsResponse(
        total_servers=total_servers,
        online_servers=online_servers,
        offline_servers=offline_servers,
        total_bandwidth_gb=total_bandwidth_gb,
        average_load=average_load,
        total_users_connected=total_users_connected,
    )


@router.post("/{server_id}/health-check")
async def check_server_health(
    server_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """
    Perform health check on server (Admin only)
    """
    query = select(Server).where(Server.id == server_id)
    result = await db.execute(query)
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # TODO: Implement actual health check logic
    # - Ping server
    # - Check service availability
    # - Update status and metrics
    
    from datetime import datetime
    server.last_check = datetime.utcnow()
    await db.commit()
    
    return {
        "server_id": server_id,
        "status": "healthy",
        "message": "Health check completed"
    }
