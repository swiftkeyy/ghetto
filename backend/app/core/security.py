"""
GHETTO VPN - Security Module
Handles authentication, password hashing, JWT tokens, and encryption
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings


# ============================================
# Password Hashing (Argon2)
# ============================================

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=settings.argon2_time_cost,
    argon2__memory_cost=settings.argon2_memory_cost,
    argon2__parallelism=settings.argon2_parallelism,
)


def hash_password(password: str) -> str:
    """
    Hash password using Argon2
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================
# JWT Token Management
# ============================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify token and check type
    
    Args:
        token: JWT token string
        token_type: Expected token type (access or refresh)
        
    Returns:
        Decoded payload if valid, None otherwise
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    if payload.get("type") != token_type:
        return None
    
    return payload


# ============================================
# Random Token Generation
# ============================================

def generate_random_token(length: int = 32) -> str:
    """
    Generate cryptographically secure random token
    
    Args:
        length: Token length in bytes
        
    Returns:
        Hex-encoded random token
    """
    return secrets.token_hex(length)


def generate_referral_code(length: int = 8) -> str:
    """
    Generate referral code (alphanumeric, uppercase)
    
    Args:
        length: Code length
        
    Returns:
        Random referral code
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_api_key() -> str:
    """
    Generate API key for external integrations
    
    Returns:
        Random API key with prefix
    """
    return f"gvpn_{secrets.token_urlsafe(32)}"


# ============================================
# Two-Factor Authentication
# ============================================

def generate_2fa_secret() -> str:
    """
    Generate 2FA secret for TOTP
    
    Returns:
        Base32 encoded secret
    """
    return secrets.token_hex(20)


# ============================================
# Data Encryption (for sensitive configs)
# ============================================

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64


def get_encryption_key() -> bytes:
    """
    Derive encryption key from secret key
    
    Returns:
        Fernet encryption key
    """
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ghetto_vpn_salt",  # In production, use environment variable
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.secret_key.encode()))
    return key


def encrypt_data(data: str) -> str:
    """
    Encrypt sensitive data (e.g., VPN private keys)
    
    Args:
        data: Plain text data
        
    Returns:
        Encrypted data (base64 encoded)
    """
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(data.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt sensitive data
    
    Args:
        encrypted_data: Encrypted data (base64 encoded)
        
    Returns:
        Decrypted plain text
    """
    f = Fernet(get_encryption_key())
    decoded = base64.b64decode(encrypted_data.encode())
    decrypted = f.decrypt(decoded)
    return decrypted.decode()


# ============================================
# Admin Authentication Helpers
# ============================================

def create_admin_tokens(admin_id: int, email: str) -> Dict[str, str]:
    """
    Create access and refresh tokens for admin
    
    Args:
        admin_id: Admin ID
        email: Admin email
        
    Returns:
        Dict with access_token and refresh_token
    """
    token_data = {
        "sub": str(admin_id),
        "email": email,
        "role": "admin"
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


# ============================================
# Security Utilities
# ============================================

def validate_telegram_data(data: Dict[str, Any], token: str) -> bool:
    """
    Validate Telegram widget login data
    
    Args:
        data: Telegram auth data
        token: Bot token
        
    Returns:
        True if valid, False otherwise
    """
    import hmac
    import hashlib
    
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False
    
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(data.items())])
    secret_key = hashlib.sha256(token.encode()).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return calculated_hash == check_hash


def is_strong_password(password: str) -> bool:
    """
    Check if password meets strength requirements
    
    Args:
        password: Password to check
        
    Returns:
        True if strong, False otherwise
    """
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return all([has_upper, has_lower, has_digit, has_special])
