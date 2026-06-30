"""
VPN Server SSH Manager - Automatic key management via SSH
"""

import asyncio
import asyncssh
import json
import secrets
from typing import Optional, Dict, Any
from datetime import datetime

from src.core.config import settings
from src.domain.models import Server, User, Device


class SSHServerManager:
    """Управление VPN серверами через SSH"""
    
    def __init__(self, server: Server):
        self.server = server
        self.host = server.ip_address
        self.port = server.config.get('ssh_port', 22)
        self.username = server.config.get('ssh_username', 'root')
        self.password = server.config.get('ssh_password')
        self.private_key = server.config.get('ssh_private_key')
    
    async def connect(self) -> asyncssh.SSHClientConnection:
        """Подключение к серверу через SSH"""
        try:
            if self.private_key:
                # Подключение по ключу (рекомендуется)
                conn = await asyncssh.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    client_keys=[self.private_key],
                    known_hosts=None
                )
            else:
                # Подключение по паролю
                conn = await asyncssh.connect(
                    self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    known_hosts=None
                )
            return conn
        except Exception as e:
            raise Exception(f"SSH connection failed: {str(e)}")
    
    async def execute_command(self, command: str) -> str:
        """Выполнить команду на сервере"""
        async with await self.connect() as conn:
            result = await conn.run(command, check=True)
            return result.stdout
    
    # ========================================================================
    # WIREGUARD MANAGEMENT
    # ========================================================================
    
    async def create_wireguard_peer(self, user: User, device: Device) -> Dict[str, str]:
        """
        Создать WireGuard peer на сервере
        Возвращает: {private_key, public_key, ip_address, config}
        """
        try:
            # Генерация ключей
            private_key_cmd = "wg genkey"
            private_key = (await self.execute_command(private_key_cmd)).strip()
            
            # Генерация публичного ключа
            public_key_cmd = f"echo {private_key} | wg pubkey"
            public_key = (await self.execute_command(public_key_cmd)).strip()
            
            # Получение следующего доступного IP
            ip_address = await self._get_next_wireguard_ip()
            
            # Добавление peer в конфигурацию
            peer_config = f"""
[Peer]
PublicKey = {public_key}
AllowedIPs = {ip_address}/32
"""
            
            # Добавить peer в wg0.conf
            add_peer_cmd = f"echo '{peer_config}' >> /etc/wireguard/wg0.conf"
            await self.execute_command(add_peer_cmd)
            
            # Применить изменения
            await self.execute_command("wg syncconf wg0 <(wg-quick strip wg0)")
            
            # Получить публичный ключ сервера
            server_pubkey_cmd = "cat /etc/wireguard/server_public.key"
            server_public_key = (await self.execute_command(server_pubkey_cmd)).strip()
            
            # Создать клиентский конфиг
            client_config = f"""[Interface]
PrivateKey = {private_key}
Address = {ip_address}/32
DNS = {settings.WIREGUARD_DNS}
MTU = 1280

[Peer]
PublicKey = {server_public_key}
Endpoint = {self.host}:{self.server.port}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
            
            return {
                "private_key": private_key,
                "public_key": public_key,
                "ip_address": ip_address,
                "config": client_config,
                "server_public_key": server_public_key
            }
            
        except Exception as e:
            raise Exception(f"Failed to create WireGuard peer: {str(e)}")
    
    async def _get_next_wireguard_ip(self) -> str:
        """Получить следующий свободный IP для WireGuard"""
        try:
            # Получить все используемые IP
            cmd = "wg show wg0 allowed-ips | awk '{print $2}'"
            used_ips = await self.execute_command(cmd)
            
            # Парсинг используемых IP
            used_list = [ip.split('/')[0] for ip in used_ips.strip().split('\n') if ip]
            
            # Найти свободный IP в диапазоне 10.0.0.2 - 10.0.0.254
            for i in range(2, 255):
                ip = f"10.0.0.{i}"
                if ip not in used_list:
                    return ip
            
            raise Exception("No available IPs in range")
        except Exception as e:
            # Fallback - случайный IP
            return f"10.0.0.{secrets.randbelow(253) + 2}"
    
    async def remove_wireguard_peer(self, public_key: str) -> bool:
        """Удалить WireGuard peer"""
        try:
            # Удалить peer
            cmd = f"wg set wg0 peer {public_key} remove"
            await self.execute_command(cmd)
            
            # Удалить из конфига
            remove_cmd = f"sed -i '/PublicKey = {public_key}/,+1d' /etc/wireguard/wg0.conf"
            await self.execute_command(remove_cmd)
            
            return True
        except Exception as e:
            print(f"Failed to remove WireGuard peer: {str(e)}")
            return False
    
    # ========================================================================
    # XRAY (VLESS) MANAGEMENT
    # ========================================================================
    
    async def create_xray_user(self, user: User, device: Device) -> Dict[str, str]:
        """
        Создать VLESS пользователя в Xray
        Возвращает: {uuid, config, import_link}
        """
        try:
            import uuid as uuid_lib
            
            # Генерация UUID
            user_uuid = str(uuid_lib.uuid4())
            
            # Добавить пользователя в конфиг Xray
            config_path = "/usr/local/etc/xray/config.json"
            
            # Прочитать текущий конфиг
            read_cmd = f"cat {config_path}"
            current_config = await self.execute_command(read_cmd)
            
            # Парсинг JSON
            config_data = json.loads(current_config)
            
            # Найти inbound с VLESS
            for inbound in config_data.get('inbounds', []):
                if inbound.get('protocol') == 'vless':
                    # Добавить пользователя
                    if 'settings' not in inbound:
                        inbound['settings'] = {}
                    if 'clients' not in inbound['settings']:
                        inbound['settings']['clients'] = []
                    
                    inbound['settings']['clients'].append({
                        "id": user_uuid,
                        "email": f"user_{user.id}_device_{device.id}",
                        "flow": settings.VLESS_FLOW
                    })
                    break
            
            # Сохранить конфиг
            new_config = json.dumps(config_data, indent=2)
            save_cmd = f"echo '{new_config}' > {config_path}"
            await self.execute_command(save_cmd)
            
            # Перезапустить Xray
            await self.execute_command("systemctl restart xray")
            
            # Получить параметры для клиента
            server_config = self.server.config or {}
            sni = server_config.get('sni', 'www.google.com')
            public_key = server_config.get('public_key', '')
            short_id = server_config.get('short_id', '')
            
            # Создать VLESS URI
            vless_uri = (
                f"vless://{user_uuid}@{self.host}:{self.server.port}"
                f"?security=reality"
                f"&sni={sni}"
                f"&fp=chrome"
                f"&pbk={public_key}"
                f"&sid={short_id}"
                f"&type=tcp"
                f"&flow={settings.VLESS_FLOW}"
                f"#{self.server.name}"
            )
            
            return {
                "uuid": user_uuid,
                "config": new_config,
                "import_link": vless_uri,
                "server_name": self.server.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to create Xray user: {str(e)}")
    
    async def remove_xray_user(self, user_uuid: str) -> bool:
        """Удалить VLESS пользователя"""
        try:
            config_path = "/usr/local/etc/xray/config.json"
            
            # Прочитать конфиг
            read_cmd = f"cat {config_path}"
            current_config = await self.execute_command(read_cmd)
            
            # Парсинг JSON
            config_data = json.loads(current_config)
            
            # Найти и удалить пользователя
            for inbound in config_data.get('inbounds', []):
                if inbound.get('protocol') == 'vless':
                    clients = inbound.get('settings', {}).get('clients', [])
                    inbound['settings']['clients'] = [
                        c for c in clients if c.get('id') != user_uuid
                    ]
            
            # Сохранить конфиг
            new_config = json.dumps(config_data, indent=2)
            save_cmd = f"echo '{new_config}' > {config_path}"
            await self.execute_command(save_cmd)
            
            # Перезапустить Xray
            await self.execute_command("systemctl restart xray")
            
            return True
        except Exception as e:
            print(f"Failed to remove Xray user: {str(e)}")
            return False
    
    # ========================================================================
    # SERVER STATUS & MONITORING
    # ========================================================================
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Получить статус сервера"""
        try:
            # CPU usage
            cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
            cpu_usage = float(await self.execute_command(cpu_cmd))
            
            # RAM usage
            ram_cmd = "free | grep Mem | awk '{print ($3/$2) * 100.0}'"
            ram_usage = float(await self.execute_command(ram_cmd))
            
            # Disk usage
            disk_cmd = "df -h / | awk 'NR==2 {print $5}' | cut -d'%' -f1"
            disk_usage = float(await self.execute_command(disk_cmd))
            
            # Network traffic
            rx_cmd = "cat /sys/class/net/eth0/statistics/rx_bytes"
            tx_cmd = "cat /sys/class/net/eth0/statistics/tx_bytes"
            rx_bytes = int(await self.execute_command(rx_cmd))
            tx_bytes = int(await self.execute_command(tx_cmd))
            
            # Connected users (WireGuard)
            wg_users_cmd = "wg show wg0 peers | wc -l"
            connected_users = int(await self.execute_command(wg_users_cmd))
            
            return {
                "status": "online",
                "cpu_usage": cpu_usage,
                "ram_usage": ram_usage,
                "disk_usage": disk_usage,
                "rx_bytes": rx_bytes,
                "tx_bytes": tx_bytes,
                "connected_users": connected_users,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> bool:
        """Проверка работоспособности сервера"""
        try:
            # Ping test
            await self.execute_command("echo 'pong'")
            
            # Check WireGuard
            wg_check = await self.execute_command("systemctl is-active wg-quick@wg0")
            if "active" not in wg_check:
                return False
            
            # Check Xray (if enabled)
            if settings.XRAY_ENABLED:
                xray_check = await self.execute_command("systemctl is-active xray")
                if "active" not in xray_check:
                    return False
            
            return True
        except Exception as e:
            print(f"Health check failed: {str(e)}")
            return False
    
    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================
    
    async def sync_all_users(self) -> Dict[str, int]:
        """Синхронизировать всех пользователей с сервером"""
        try:
            # TODO: Реализовать синхронизацию всех пользователей
            # Получить список текущих peers
            # Сравнить с базой данных
            # Удалить неактивных
            # Добавить новых
            
            return {
                "added": 0,
                "removed": 0,
                "errors": 0
            }
        except Exception as e:
            raise Exception(f"Sync failed: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def create_vpn_config_for_device(
    server: Server,
    user: User,
    device: Device
) -> Dict[str, str]:
    """
    Главная функция для создания VPN конфига через SSH
    Автоматически определяет протокол и создает ключи
    """
    manager = SSHServerManager(server)
    
    if server.protocol.value == "wireguard":
        return await manager.create_wireguard_peer(user, device)
    elif server.protocol.value == "vless":
        return await manager.create_xray_user(user, device)
    else:
        raise Exception(f"Protocol {server.protocol.value} not supported for SSH management")


async def remove_vpn_config_for_device(
    server: Server,
    device: Device
) -> bool:
    """Удалить VPN конфиг с сервера"""
    manager = SSHServerManager(server)
    
    if server.protocol.value == "wireguard" and device.public_key:
        return await manager.remove_wireguard_peer(device.public_key)
    elif server.protocol.value == "vless" and device.config:
        # Извлечь UUID из конфига
        # TODO: Реализовать извлечение UUID
        return await manager.remove_xray_user("uuid")
    
    return False


async def check_server_health(server: Server) -> bool:
    """Проверить здоровье сервера"""
    manager = SSHServerManager(server)
    return await manager.health_check()


async def get_server_statistics(server: Server) -> Dict[str, Any]:
    """Получить статистику сервера"""
    manager = SSHServerManager(server)
    return await manager.get_server_status()
