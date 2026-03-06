"""VLESS (vless://) 解析器"""
from urllib.parse import urlparse, parse_qs, unquote
from src.parsers.base import BaseParser
from src.models.node import Node
from loguru import logger


class VLESSParser(BaseParser):
    """VLESS (vless://) 协议解析器"""

    def can_parse(self, uri: str) -> bool:
        return uri.startswith("vless://")

    def parse(self, uri: str) -> Node:
        """解析vless://格式URI

        格式: vless://uuid@host:port?type=tcp&security=tls&sni=xxx#remarks
        """
        if not uri.startswith("vless://"):
            raise ValueError(f"无效的vless URI: {uri}")

        parsed = urlparse(uri)
        uuid = unquote(parsed.username or "")
        host = parsed.hostname or ""
        port = parsed.port or 443

        if not host:
            raise ValueError("vless URI缺少服务器地址")
        if not uuid:
            raise ValueError("vless URI缺少uuid")
        if not (1 <= port <= 65535):
            raise ValueError(f"端口超出范围: {port}")

        query = parse_qs(parsed.query)
        transport = query.get("type", [None])[0]
        security = query.get("security", ["none"])[0]
        tls = security in ("tls", "reality")
        sni = query.get("sni", [None])[0] or query.get("peer", [None])[0]
        remarks = unquote(parsed.fragment) if parsed.fragment else None

        logger.debug(f"vless节点解析成功: {host}:{port}")
        return Node(
            protocol="vless",
            host=host,
            port=port,
            uuid=uuid,
            transport=transport,
            tls=tls,
            sni=sni,
            remarks=remarks,
        )
