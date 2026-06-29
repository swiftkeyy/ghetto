"""
Authentication and Authorization Dependencies
"""

from typing import Optional
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.infrastructure.database import get_db
from src.domain.models import User, UserStatus


# Security scheme
security = HTTPBearer()


# ============================================================================
# JWT TOKEN OPERATIONS
# ============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# USER AUTHENTICATION
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id: Optional[int] = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Check if user is blocked
    if user.status == UserStatus.BLOCKED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked"
        )
    
    # Update last activity
    user.last_activity = datetime.utcnow()
    await db.commit()
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (not blocked or suspended)
    """
    if current_user.status not in [UserStatus.ACTIVE, UserStatus.TRIAL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    return current_user


async def get_current_premium_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current premium user (has active subscription)
    """
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    
    # Check if subscription is still valid
    if current_user.subscription_end and current_user.subscription_end < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription has expired"
        )
    
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current admin user
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


# ============================================================================
# API KEY AUTHENTICATION (for webhooks and external services)
# ============================================================================

async def verify_api_key(
    x_api_key: str = Header(..., description="API Key")
) -> bool:
    """
    Verify API key for webhooks and external services
    """
    # In production, store API keys in database
    valid_keys = [
        settings.SECRET_KEY,
        settings.BOT_WEBHOOK_SECRET,
    ]
    
    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True


# ============================================================================
# TELEGRAM BOT AUTHENTICATION
# ============================================================================

async def get_user_by_telegram_id(
    telegram_id: int,
    db: AsyncSession
) -> Optional[User]:
    """
    Get user by Telegram ID
    """
    query = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_user_from_telegram(
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    language_code: str,
    referred_by_code: Optional[str],
    db: AsyncSession
) -> User:
    """
    Create new user from Telegram data
    """
    import secrets
    
    # Generate unique referral code
    referral_code = secrets.token_urlsafe(8)
    
    # Find referrer if code provided
    referred_by_id = None
    if referred_by_code:
        query = select(User).where(User.referral_code == referred_by_code)
        result = await db.execute(query)
        referrer = result.scalar_one_or_none()
        if referrer:
            referred_by_id = referrer.id
    
    # Check if telegram_id is admin
    is_admin = telegram_id in settings.admin_ids
    
    # Create user
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language_code=language_code or "en",
        referral_code=referral_code,
        referred_by_id=referred_by_id,
        is_admin=is_admin,
        status=UserStatus.ACTIVE,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


# ============================================================================
# PERMISSION CHECKS
# ============================================================================

def check_device_limit(user: User, current_devices: int) -> bool:
    """Check if user can add more devices"""
    return current_devices < settings.MAX_DEVICES_PER_USER


def check_connection_limit(user: User, current_connections: int) -> bool:
    """Check if user can create more connections"""
    return current_connections < settings.MAX_SIMULTANEOUS_CONNECTIONS
