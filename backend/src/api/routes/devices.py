"""
Devices API Router
"""

import base64
import secrets
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_db
from src.domain.models import Device, User, Server, DevicePlatform
from src.api.schemas.device import (
    DeviceResponse,
    DeviceCreate,
    DeviceUpdate,
    DeviceListResponse,
    DeviceConfigRequest,
    DeviceConfigResponse,
    DeviceStatsResponse,
)
from src.api.dependencies.auth import (
    get_current_active_user,
    get_current_premium_user,
    check_device_limit,
)
from src.core.config import settings
from src.vpn.config_generator import ConfigGenerator

router = APIRouter()


@router.get("/", response_model=DeviceListResponse)
async def get_user_devices(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Get current user's devices
    """
    query = select(Device).where(Device.user_id == user.id).order_by(Device.created_at.desc())
    result = await db.execute(query)
    devices = result.scalars().all()
    
    remaining_slots = max(0, settings.MAX_DEVICES_PER_USER - len(devices))
    
    return DeviceListResponse(
        items=devices,
        total=len(devices),
        max_devices=settings.MAX_DEVICES_PER_USER,
        remaining_slots=remaining_slots,
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Get device by ID
    """
    query = select(Device).where(
        Device.id == device_id,
        Device.user_id == user.id
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return device


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_premium_user),
):
    """
    Create new device (Premium only)
    """
    # Check device limit
    query = select(func.count()).select_from(Device).where(Device.user_id == user.id)
    current_count = await db.scalar(query)
    
    if not check_device_limit(user, current_count):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device limit reached. Maximum {settings.MAX_DEVICES_PER_USER} devices allowed."
        )
    
    # Generate unique device ID
    device_id = f"{user.telegram_id}_{secrets.token_urlsafe(8)}"
    
    # Create device
    device = Device(
        user_id=user.id,
        name=device_data.name,
        platform=device_data.platform,
        device_id=device_id,
        is_active=True,
    )
    
    db.add(device)
    await db.commit()
    await db.refresh(device)
    
    return device


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Update device
    """
    query = select(Device).where(
        Device.id == device_id,
        Device.user_id == user.id
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Update fields
    for field, value in device_data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    
    await db.commit()
    await db.refresh(device)
    
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Delete device and remove keys from VPS
    """
    query = select(Device).where(
        Device.id == device_id,
        Device.user_id == user.id
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Try to remove keys from all servers
    if device.public_key or device.config:
        from src.vpn.ssh_manager import remove_vpn_config_for_device
        
        # Get all servers and try to remove from each
        query = select(Server).where(Server.is_active == True)
        result = await db.execute(query)
        servers = result.scalars().all()
        
        for server in servers:
            if server.config and server.config.get('ssh_enabled'):
                try:
                    await remove_vpn_config_for_device(server, device)
                except Exception as e:
                    # Log error but continue deletion
                    print(f"Failed to remove device from server {server.id}: {str(e)}")
    
    await db.delete(device)
    await db.commit()
    
    return None


@router.post("/{device_id}/config", response_model=DeviceConfigResponse)
async def get_device_config(
    device_id: int,
    config_request: DeviceConfigRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_premium_user),
):
    """
    Generate VPN configuration for device
    """
    # Get device
    query = select(Device).where(
        Device.id == device_id,
        Device.user_id == user.id
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get server
    query = select(Server).where(Server.id == config_request.server_id)
    result = await db.execute(query)
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Generate configuration via SSH if server has SSH credentials
    if server.config and server.config.get('ssh_enabled'):
        # Use SSH manager to create keys directly on VPS
        from src.vpn.ssh_manager import create_vpn_config_for_device
        
        try:
            ssh_config = await create_vpn_config_for_device(server, user, device)
            
            # Save keys to device
            device.public_key = ssh_config.get('public_key')
            device.private_key = ssh_config.get('private_key')
            
            config_data = {
                "config_base64": base64.b64encode(ssh_config['config'].encode()).decode(),
                "import_link": ssh_config.get('import_link', ''),
                "qr_code_base64": "",  # Will be generated below
                "instructions": "",
                "app_download_link": ""
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create VPN config on server: {str(e)}"
            )
    else:
        # Generate configuration locally (old method)
        config_generator = ConfigGenerator(
            user=user,
            device=device,
            server=server,
            platform=config_request.platform
        )
        
        config_data = await config_generator.generate()
    
    # Generate QR code for any method
    from src.vpn.config_generator import QRCodeGenerator
    qr_code_data = config_data.get('import_link') or base64.b64decode(config_data['config_base64']).decode()
    config_data['qr_code_base64'] = QRCodeGenerator.generate_base64(qr_code_data, style='neon')
    
    # Get instructions
    from src.vpn.config_generator import InstructionsGenerator
    config_data['instructions'] = InstructionsGenerator.get_instructions(config_request.platform, server.protocol)
    config_data['app_download_link'] = InstructionsGenerator.get_app_download_link(config_request.platform)
    
    # Save config to device
    device.config = config_data["config_base64"]
    device.updated_at = datetime.utcnow()
    await db.commit()
    
    return DeviceConfigResponse(
        config=config_data["config_base64"],
        qr_code=config_data["qr_code_base64"],
        import_link=config_data["import_link"],
        instructions=config_data["instructions"],
        app_download_link=config_data["app_download_link"],
    )


@router.get("/{device_id}/stats", response_model=DeviceStatsResponse)
async def get_device_stats(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    """
    Get device statistics
    """
    from src.domain.models import Connection
    
    query = select(Device).where(
        Device.id == device_id,
        Device.user_id == user.id
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Get connection statistics
    query = select(Connection).where(Connection.device_id == device_id)
    result = await db.execute(query)
    connections = result.scalars().all()
    
    total_connections = len(connections)
    
    # Calculate average session duration
    durations = [c.duration_seconds for c in connections if c.duration_seconds]
    avg_duration = sum(durations) / len(durations) if durations else 0
    avg_duration_minutes = avg_duration / 60
    
    return DeviceStatsResponse(
        device_id=device_id,
        total_bandwidth_gb=device.total_bandwidth,
        total_connections=total_connections,
        last_connected=device.last_connection,
        average_session_duration_minutes=avg_duration_minutes if avg_duration_minutes > 0 else None,
    )


# ============================================================================
# CONFIG GENERATOR CLASS
# ============================================================================

class ConfigGenerator:
    """VPN Configuration Generator for different platforms"""
    
    def __init__(self, user: User, device: Device, server: Server, platform: DevicePlatform):
        self.user = user
        self.device = device
        self.server = server
        self.platform = platform
    
    async def generate(self) -> dict:
        """Generate configuration based on protocol and platform"""
        
        if self.server.protocol.value == "wireguard":
            return await self._generate_wireguard()
        elif self.server.protocol.value == "vless":
            return await self._generate_vless()
        elif self.server.protocol.value == "vmess":
            return await self._generate_vmess()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Protocol {self.server.protocol.value} not supported yet"
            )
    
    async def _generate_wireguard(self) -> dict:
        """Generate WireGuard configuration"""
        
        # Generate keys if not exist
        if not self.device.private_key:
            # TODO: Generate actual WireGuard keys
            private_key = secrets.token_urlsafe(32)
            public_key = secrets.token_urlsafe(32)
            self.device.private_key = private_key
            self.device.public_key = public_key
        
        # Create WireGuard config
        config = f"""[Interface]
PrivateKey = {self.device.private_key}
Address = 10.0.0.{self.user.id % 254 + 1}/32
DNS = {settings.WIREGUARD_DNS}

[Peer]
PublicKey = {self.server.config.get('public_key', 'SERVER_PUBLIC_KEY')}
Endpoint = {self.server.ip_address}:{self.server.port}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
        
        # Base64 encode
        config_base64 = base64.b64encode(config.encode()).decode()
        
        # Generate QR code
        import qrcode
        from io import BytesIO
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(config)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#00FF9F", back_color="#0A0A0A")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Import link
        import_link = f"wireguard://import#{config_base64}"
        
        # Instructions based on platform
        instructions = self._get_instructions(self.platform, "wireguard")
        
        # App download link
        app_download_link = self._get_app_link(self.platform)
        
        return {
            "config_base64": config_base64,
            "qr_code_base64": qr_code_base64,
            "import_link": import_link,
            "instructions": instructions,
            "app_download_link": app_download_link,
        }
    
    async def _generate_vless(self) -> dict:
        """Generate VLESS configuration"""
        
        # VLESS URI format
        uuid = secrets.token_urlsafe(16)
        
        vless_uri = (
            f"vless://{uuid}@{self.server.ip_address}:{self.server.port}"
            f"?security=reality&sni={self.server.config.get('sni', 'www.google.com')}"
            f"&fp=chrome&pbk={self.server.config.get('public_key', '')}"
            f"&type=tcp&flow={settings.VLESS_FLOW}"
            f"#{self.server.name}"
        )
        
        config_base64 = base64.b64encode(vless_uri.encode()).decode()
        
        # Generate QR code
        import qrcode
        from io import BytesIO
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(vless_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#00FF9F", back_color="#0A0A0A")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        instructions = self._get_instructions(self.platform, "vless")
        app_download_link = self._get_app_link(self.platform)
        
        return {
            "config_base64": config_base64,
            "qr_code_base64": qr_code_base64,
            "import_link": vless_uri,
            "instructions": instructions,
            "app_download_link": app_download_link,
        }
    
    async def _generate_vmess(self) -> dict:
        """Generate VMess configuration"""
        # TODO: Implement VMess generation
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="VMess generation not implemented yet"
        )
    
    def _get_instructions(self, platform: DevicePlatform, protocol: str) -> str:
        """Get setup instructions for platform"""
        
        instructions = {
            DevicePlatform.ANDROID: """
📱 Инструкция для Android (Happ):

1️⃣ Скачайте приложение Happ из Google Play
2️⃣ Откройте приложение
3️⃣ Нажмите на "+" в правом верхнем углу
4️⃣ Выберите "Import from QR code"
5️⃣ Отсканируйте QR-код выше
6️⃣ Нажмите "Connect"

✅ Готово! Вы подключены к VPN
""",
            DevicePlatform.IOS: """
🍎 Инструкция для iOS (Happ):

1️⃣ Скачайте приложение Happ из App Store
2️⃣ Откройте приложение
3️⃣ Нажмите "Add Configuration"
4️⃣ Отсканируйте QR-код или используйте ссылку
5️⃣ Разрешите добавление VPN профиля
6️⃣ Нажмите "Connect"

✅ Готово! Вы подключены к VPN
""",
            DevicePlatform.ANDROID_TV: """
📺 Инструкция для Android TV (Happ):

1️⃣ Установите Happ из Google Play на TV
2️⃣ Откройте приложение
3️⃣ Выберите "Import Configuration"
4️⃣ Отсканируйте QR-код с телефона или введите ссылку
5️⃣ Нажмите "Connect"

✅ Готово! Ваш Android TV защищен VPN
""",
            DevicePlatform.WINDOWS: """
💻 Инструкция для Windows (Hiddify):

1️⃣ Скачайте Hiddify для Windows
2️⃣ Установите и запустите приложение
3️⃣ Нажмите "Add Configuration"
4️⃣ Вставьте ссылку импорта или импортируйте файл
5️⃣ Нажмите "Connect"

✅ Готово! Ваш компьютер защищен VPN
""",
        }
        
        return instructions.get(platform, "Instructions not available")
    
    def _get_app_link(self, platform: DevicePlatform) -> str:
        """Get app download link for platform"""
        
        links = {
            DevicePlatform.ANDROID: "https://play.google.com/store/apps/details?id=app.hiddify.com",
            DevicePlatform.IOS: "https://apps.apple.com/app/hiddify/id6596777532",
            DevicePlatform.ANDROID_TV: "https://play.google.com/store/apps/details?id=app.hiddify.com",
            DevicePlatform.WINDOWS: "https://github.com/hiddify/hiddify-next/releases",
        }
        
        return links.get(platform, "")
