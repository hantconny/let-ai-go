"""节点数据模型 - 代理节点的所有属性定义"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from src.utils.hash_generator import generate_node_id


@dataclass
class Node:
    """代理节点数据模型，包含17个属性"""

    protocol: str
    host: str
    port: int
    # 可选字段
    tls: bool = False
    sni: Optional[str] = None
    uuid: Optional[str] = None
    password: Optional[str] = None
    cipher: Optional[str] = None
    transport: Optional[str] = None
    network: Optional[str] = None
    auth_protocol: Optional[str] = None
    obfuscation: Optional[str] = None
    remarks: Optional[str] = None
    source_id: Optional[str] = None
    parsed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # 自动生成
    node_id: str = field(init=False)

    def __post_init__(self):
        """初始化后自动生成node_id"""
        self.node_id = generate_node_id(self.protocol, self.host, self.port)

    def to_dict(self) -> dict:
        """将节点转换为字典"""
        return {
            "node_id": self.node_id,
            "protocol": self.protocol,
            "host": self.host,
            "port": self.port,
            "tls": self.tls,
            "sni": self.sni,
            "uuid": self.uuid,
            "password": self.password,
            "cipher": self.cipher,
            "transport": self.transport,
            "network": self.network,
            "auth_protocol": self.auth_protocol,
            "obfuscation": self.obfuscation,
            "remarks": self.remarks,
            "source_id": self.source_id,
            "parsed_at": self.parsed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        """从字典创建节点对象"""
        parsed_at = data.get("parsed_at")
        if isinstance(parsed_at, str):
            parsed_at = datetime.fromisoformat(parsed_at)
        elif parsed_at is None:
            parsed_at = datetime.now(timezone.utc)

        node = cls(
            protocol=data["protocol"],
            host=data["host"],
            port=int(data["port"]),
            tls=str(data.get("tls", "false")).lower() == "true",
            sni=data.get("sni") or None,
            uuid=data.get("uuid") or None,
            password=data.get("password") or None,
            cipher=data.get("cipher") or None,
            transport=data.get("transport") or None,
            network=data.get("network") or None,
            auth_protocol=data.get("auth_protocol") or None,
            obfuscation=data.get("obfuscation") or None,
            remarks=data.get("remarks") or None,
            source_id=data.get("source_id") or None,
            parsed_at=parsed_at,
        )
        return node
