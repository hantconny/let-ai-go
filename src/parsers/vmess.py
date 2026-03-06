"""VMess (vmess://) 解析器"""
import base64
import json
from src.parsers.base import BaseParser
from src.models.node import Node
from loguru import logger


class VMessParser(BaseParser):
    """VMess (vmess://) 协议解析器"""

    def can_parse(self, uri: str) -> bool:
        return uri.startswith("vmess://")

    def parse(self, uri: str) -> Node:
        """解析vmess://格式URI

        格式: vmess://base64(json_config)
        """
        if not uri.startswith("vmess://"):
            raise ValueError(f"无效的vmess URI: {uri}")

        encoded = uri[8:]  # 去除 vmess://

        # 补全base64填充
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += "=" * padding

        try:
            decoded = base64.b64decode(encoded).decode("utf-8")
            config = json.loads(decoded)
        except Exception as e:
            raise ValueError(f"vmess配置解码失败: {e}")

        host = config.get("add", "")
        port_raw = config.get("port", 0)
        uuid = config.get("id", "")

        if not host:
            raise ValueError("vmess配置缺少服务器地址")
        if not uuid:
            raise ValueError("vmess配置缺少uuid")

        try:
            port = int(port_raw)
        except (ValueError, TypeError):
            raise ValueError(f"无效的端口: {port_raw}")

        if not (1 <= port <= 65535):
            raise ValueError(f"端口超出范围: {port}")

        tls_raw = str(config.get("tls", "")).lower()
        tls = tls_raw in ("tls", "true", "1")

        logger.debug(f"vmess节点解析成功: {host}:{port}")
        return Node(
            protocol="vmess",
            host=host,
            port=port,
            uuid=uuid,
            cipher=config.get("scy", config.get("cipher", "auto")),
            transport=config.get("net", None),
            network=config.get("type", None),
            tls=tls,
            sni=config.get("sni", config.get("host", None)) or None,
            remarks=config.get("ps", None),
        )
