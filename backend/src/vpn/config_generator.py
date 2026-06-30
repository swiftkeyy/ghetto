"""
VPN Core Module - Protocol Configuration Generators
"""

import base64
import secrets
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from src.domain.models import Server, User, Device, VPNProtocol, DevicePlatform
from src.core.config import settings


class VPNConfigGenerator(ABC):
    """Abstract base class for VPN configuration generators"""
    
    def __init__(self, server: Server, user: User, device: Device):
        self.server = server
        self.user = user
        self.device = device
    
    @abstractmethod
    async def generate_config(self) -> Dict[str, Any]:
        """Generate VPN configuration"""
        pass
    
    @abstractmethod
    async def generate_uri(self) -> str:
        """Generate import URI/link"""
        pass


# ============================================================================
# WIREGUARD
# ============================================================================

class WireGuardGenerator(VPNConfigGenerator):
    """WireGuard configuration generator"""
    
    async def generate_config(self) -> Dict[str, Any]:
        """Generate WireGuard configuration"""
        
        # Generate keys if not exist
        if not self.device.private_key or not self.device.public_key:
            private_key, public_key = self._generate_keypair()
            self.device.private_key = private_key
            self.device.public_key = public_key
        
        # Assign IP address based on user ID
        client_ip = self._get_client_ip()
        
        # Get server public key from config
        server_public_key = self.server.config.get('public_key', 'SERVER_PUBLIC_KEY_PLACEHOLDER')
        
        # DNS servers
        dns_servers = settings.WIREGUARD_DNS
        
        # Build configuration
        config = f"""[Interface]
PrivateKey = {self.device.private_key}
Address = {client_ip}/32
DNS = {dns_servers}
MTU = 1280

[Peer]
PublicKey = {server_public_key}
Endpoint = {self.server.ip_address}:{self.server.port}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
        
        return {
            "config": config,
            "format": "wireguard",
            "client_ip": client_ip,
            "server_endpoint": f"{self.server.ip_address}:{self.server.port}",
        }
    
    async def generate_uri(self) -> str:
        """Generate WireGuard import URI"""
        config_data = await self.generate_config()
        config_base64 = base64.b64encode(config_data["config"].encode()).decode()
        return f"wireguard://import#{config_base64}"
    
    def _generate_keypair(self) -> tuple[str, str]:
        """Generate WireGuard key pair"""
        # In production, use actual WireGuard key generation
        # For now, using secure random strings
        private_key = base64.b64encode(secrets.token_bytes(32)).decode()
        public_key = base64.b64encode(secrets.token_bytes(32)).decode()
        return private_key, public_key
    
    def _get_client_ip(self) -> str:
        """Get client IP address from user ID"""
        # Simple IP allocation: 10.0.0.0/8 range
        user_offset = self.user.id % 254 + 1
        device_offset = self.device.id % 254
        return f"10.0.{user_offset}.{device_offset}"


# ============================================================================
# VLESS
# ============================================================================

class VLESSGenerator(VPNConfigGenerator):
    """VLESS Reality configuration generator"""
    
    async def generate_config(self) -> Dict[str, Any]:
        """Generate VLESS configuration"""
        
        # Generate UUID for user
        uuid = self._generate_uuid()
        
        # Get server config
        server_public_key = self.server.config.get('public_key', '')
        server_short_id = self.server.config.get('short_id', '')
        server_sni = self.server.config.get('sni', 'www.google.com')
        server_fingerprint = self.server.config.get('fingerprint', 'chrome')
        
        # Build VLESS config
        config = {
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": self.server.ip_address,
                    "port": self.server.port,
                    "users": [{
                        "id": uuid,
                        "encryption": "none",
                        "flow": settings.VLESS_FLOW,
                    }]
                }]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "serverName": server_sni,
                    "fingerprint": server_fingerprint,
                    "publicKey": server_public_key,
                    "shortId": server_short_id,
                    "spiderX": ""
                }
            }
        }
        
        return {
            "config": json.dumps(config, indent=2),
            "format": "vless",
            "uuid": uuid,
            "server_endpoint": f"{self.server.ip_address}:{self.server.port}",
        }
    
    async def generate_uri(self) -> str:
        """Generate VLESS import URI"""
        config_data = await self.generate_config()
        uuid = config_data["uuid"]
        
        server_config = self.server.config or {}
        sni = server_config.get('sni', 'www.google.com')
        public_key = server_config.get('public_key', '')
        short_id = server_config.get('short_id', '')
        fingerprint = server_config.get('fingerprint', 'chrome')
        
        # Build VLESS URI
        uri = (
            f"vless://{uuid}@{self.server.ip_address}:{self.server.port}"
            f"?security=reality"
            f"&sni={sni}"
            f"&fp={fingerprint}"
            f"&pbk={public_key}"
            f"&sid={short_id}"
            f"&type=tcp"
            f"&flow={settings.VLESS_FLOW}"
            f"#{self.server.name}"
        )
        
        return uri
    
    def _generate_uuid(self) -> str:
        """Generate UUID for VLESS"""
        import uuid
        return str(uuid.uuid4())


# ============================================================================
# VMESS
# ============================================================================

class VMESSGenerator(VPNConfigGenerator):
    """VMess configuration generator"""
    
    async def generate_config(self) -> Dict[str, Any]:
        """Generate VMess configuration"""
        
        uuid = self._generate_uuid()
        alter_id = 0
        
        config = {
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": self.server.ip_address,
                    "port": self.server.port,
                    "users": [{
                        "id": uuid,
                        "alterId": alter_id,
                        "security": "auto"
                    }]
                }]
            },
            "streamSettings": {
                "network": "tcp"
            }
        }
        
        return {
            "config": json.dumps(config, indent=2),
            "format": "vmess",
            "uuid": uuid,
            "server_endpoint": f"{self.server.ip_address}:{self.server.port}",
        }
    
    async def generate_uri(self) -> str:
        """Generate VMess import URI"""
        config_data = await self.generate_config()
        
        vmess_config = {
            "v": "2",
            "ps": self.server.name,
            "add": self.server.ip_address,
            "port": str(self.server.port),
            "id": config_data["uuid"],
            "aid": "0",
            "net": "tcp",
            "type": "none",
            "host": "",
            "path": "",
            "tls": ""
        }
        
        json_str = json.dumps(vmess_config)
        encoded = base64.b64encode(json_str.encode()).decode()
        
        return f"vmess://{encoded}"
    
    def _generate_uuid(self) -> str:
        """Generate UUID for VMess"""
        import uuid
        return str(uuid.uuid4())


# ============================================================================
# SHADOWSOCKS
# ============================================================================

class ShadowsocksGenerator(VPNConfigGenerator):
    """Shadowsocks configuration generator"""
    
    async def generate_config(self) -> Dict[str, Any]:
        """Generate Shadowsocks configuration"""
        
        password = self._generate_password()
        method = "chacha20-ietf-poly1305"
        
        config = {
            "server": self.server.ip_address,
            "server_port": self.server.port,
            "password": password,
            "method": method,
            "plugin": "",
            "plugin_opts": ""
        }
        
        return {
            "config": json.dumps(config, indent=2),
            "format": "shadowsocks",
            "password": password,
            "method": method,
            "server_endpoint": f"{self.server.ip_address}:{self.server.port}",
        }
    
    async def generate_uri(self) -> str:
        """Generate Shadowsocks import URI"""
        config_data = await self.generate_config()
        
        method = config_data["method"]
        password = config_data["password"]
        
        userinfo = f"{method}:{password}"
        userinfo_encoded = base64.urlsafe_b64encode(userinfo.encode()).decode().rstrip('=')
        
        uri = f"ss://{userinfo_encoded}@{self.server.ip_address}:{self.server.port}#{self.server.name}"
        
        return uri
    
    def _generate_password(self) -> str:
        """Generate secure password"""
        return base64.urlsafe_b64encode(secrets.token_bytes(16)).decode()


# ============================================================================
# FACTORY
# ============================================================================

class VPNConfigFactory:
    """Factory for creating VPN configuration generators"""
    
    @staticmethod
    def create_generator(
        protocol: VPNProtocol,
        server: Server,
        user: User,
        device: Device
    ) -> VPNConfigGenerator:
        """Create appropriate generator based on protocol"""
        
        generators = {
            VPNProtocol.WIREGUARD: WireGuardGenerator,
            VPNProtocol.VLESS: VLESSGenerator,
            VPNProtocol.VMESS: VMESSGenerator,
            VPNProtocol.SHADOWSOCKS: ShadowsocksGenerator,
        }
        
        generator_class = generators.get(protocol)
        
        if not generator_class:
            raise ValueError(f"Unsupported protocol: {protocol.value}")
        
        return generator_class(server, user, device)


# ============================================================================
# QR CODE GENERATOR
# ============================================================================

class QRCodeGenerator:
    """QR Code generator for VPN configurations"""
    
    @staticmethod
    def generate(data: str, style: str = "default") -> bytes:
        """
        Generate QR code image
        
        Args:
            data: Data to encode (URI, config, etc.)
            style: QR code style (default, dark, neon)
        
        Returns:
            PNG image as bytes
        """
        import qrcode
        from io import BytesIO
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        # Style configuration
        if style == "neon":
            fill_color = "#00FF9F"
            back_color = "#0A0A0A"
        elif style == "dark":
            fill_color = "#FFFFFF"
            back_color = "#1A1A1A"
        else:
            fill_color = "black"
            back_color = "white"
        
        # Create image
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return buffer.getvalue()
    
    @staticmethod
    def generate_base64(data: str, style: str = "default") -> str:
        """Generate QR code and return as base64 string"""
        img_bytes = QRCodeGenerator.generate(data, style)
        return base64.b64encode(img_bytes).decode()


# ============================================================================
# PLATFORM-SPECIFIC INSTRUCTIONS
# ============================================================================

class InstructionsGenerator:
    """Generate platform-specific setup instructions"""
    
    INSTRUCTIONS = {
        DevicePlatform.ANDROID: {
            "wireguard": """📱 Инструкция для Android (WireGuard):

1️⃣ Скачайте приложение WireGuard из Google Play
2️⃣ Откройте приложение
3️⃣ Нажмите на "+" в правом нижнем углу
4️⃣ Выберите "Создать из QR-кода"
5️⃣ Отсканируйте QR-код выше
6️⃣ Нажмите на переключатель для подключения

✅ Готово! Вы подключены к VPN""",
            
            "vless": """📱 Инструкция для Android (Happ):

1️⃣ Скачайте приложение Happ из Google Play
2️⃣ Откройте приложение
3️⃣ Нажмите на "+" для добавления конфигурации
4️⃣ Выберите "Import from QR code"
5️⃣ Отсканируйте QR-код выше
6️⃣ Нажмите "Connect"

✅ Готово! Вы подключены к VPN""",
        },
        
        DevicePlatform.IOS: {
            "wireguard": """🍎 Инструкция для iOS (WireGuard):

1️⃣ Скачайте приложение WireGuard из App Store
2️⃣ Откройте приложение
3️⃣ Нажмите "Add a tunnel"
4️⃣ Выберите "Create from QR code"
5️⃣ Отсканируйте QR-код выше
6️⃣ Разрешите добавление VPN конфигурации
7️⃣ Активируйте туннель переключателем

✅ Готово! Вы подключены к VPN""",
            
            "vless": """🍎 Инструкция для iOS (Happ):

1️⃣ Скачайте приложение Happ из App Store
2️⃣ Откройте приложение
3️⃣ Нажмите "Add Configuration"
4️⃣ Выберите "Scan QR Code"
5️⃣ Отсканируйте QR-код выше
6️⃣ Разрешите добавление VPN профиля
7️⃣ Нажмите "Connect"

✅ Готово! Вы подключены к VPN""",
        },
        
        DevicePlatform.ANDROID_TV: {
            "wireguard": """📺 Инструкция для Android TV:

1️⃣ Установите WireGuard из Google Play на TV
2️⃣ Откройте приложение на ТВ
3️⃣ Используйте телефон для сканирования QR-кода
4️⃣ Или введите конфигурацию вручную с помощью пульта
5️⃣ Активируйте туннель

✅ Готово! Ваш Android TV защищен VPN""",
            
            "vless": """📺 Инструкция для Android TV (Happ):

1️⃣ Установите Happ из Google Play на TV
2️⃣ Откройте приложение
3️⃣ Выберите "Import Configuration"
4️⃣ Отсканируйте QR-код с телефона
5️⃣ Или введите ссылку импорта
6️⃣ Нажмите "Connect"

✅ Готово! Ваш Android TV защищен VPN""",
        },
        
        DevicePlatform.WINDOWS: {
            "wireguard": """💻 Инструкция для Windows:

1️⃣ Скачайте WireGuard для Windows с официального сайта
2️⃣ Установите и запустите приложение
3️⃣ Нажмите "Add Tunnel" → "Add empty tunnel"
4️⃣ Скопируйте конфигурацию из текстового поля ниже
5️⃣ Вставьте в окно WireGuard
6️⃣ Нажмите "Save" и "Activate"

✅ Готово! Ваш компьютер защищен VPN""",
            
            "vless": """💻 Инструкция для Windows (Hiddify):

1️⃣ Скачайте Hiddify для Windows
2️⃣ Установите и запустите приложение
3️⃣ Нажмите "Add Configuration"
4️⃣ Вставьте ссылку импорта из буфера обмена
5️⃣ Или импортируйте файл конфигурации
6️⃣ Нажмите "Connect"

✅ Готово! Ваш компьютер защищен VPN""",
        },
    }
    
    @staticmethod
    def get_instructions(platform: DevicePlatform, protocol: VPNProtocol) -> str:
        """Get instructions for platform and protocol"""
        
        # Map protocol to instruction key
        protocol_key = protocol.value
        if protocol in [VPNProtocol.VLESS, VPNProtocol.VMESS, VPNProtocol.SHADOWSOCKS]:
            protocol_key = "vless"
        elif protocol == VPNProtocol.WIREGUARD:
            protocol_key = "wireguard"
        
        instructions = InstructionsGenerator.INSTRUCTIONS.get(platform, {}).get(protocol_key)
        
        if not instructions:
            return "Инструкции для данной платформы в разработке."
        
        return instructions
    
    @staticmethod
    def get_app_download_link(platform: DevicePlatform) -> str:
        """Get app download link for platform"""
        
        links = {
            DevicePlatform.ANDROID: "https://play.google.com/store/apps/details?id=app.hiddify.com",
            DevicePlatform.IOS: "https://apps.apple.com/app/hiddify/id6596777532",
            DevicePlatform.ANDROID_TV: "https://play.google.com/store/apps/details?id=app.hiddify.com",
            DevicePlatform.WINDOWS: "https://github.com/hiddify/hiddify-next/releases",
            DevicePlatform.MACOS: "https://github.com/hiddify/hiddify-next/releases",
            DevicePlatform.LINUX: "https://github.com/hiddify/hiddify-next/releases",
        }
        
        return links.get(platform, "")
        
class ConfigGenerator:
    def __init__(self, user, device, server, platform):
        self.generator = VPNConfigFactory.create_generator(
            protocol=server.protocol,
            server=server,
            user=user,
            device=device,
        )

    async def generate(self):
        config = await self.generator.generate_config()
        uri = await self.generator.generate_uri()

        config["uri"] = uri
        return config
