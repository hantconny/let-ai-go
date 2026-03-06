"""Hysteria (hysteria://) 解析器"""
from urllib.parse import urlparse, parse_qs, unquote
from src.parsers.base import BaseParser
from src.models.node import Node
from loguru import logger


class HysteriaParser(BaseParser):
    """Hysteria (hysteria://) 协议解析器"""

    def can_parse(self, uri: str) -> bool:
        return uri.startswith("hysteria://")

    def parse(self, uri: str) -> Node:
        """解析hysteria://格式URI

        格式: hysteria://host:port?auth=password&peer=sni#remarks
        """
        if not uri.startswith("hysteria://"):
            raise ValueError(f"无效的hysteria URI: {uri}")

        parsed = urlparse(uri)
        host = parsed.hostname or ""
        port = parsed.port or 443

        if not host:
            raise ValueError("hysteria URI缺少服务器地址")
        if not (1 <= port <= 65535):
            raise ValueError(f"端口超出范围: {port}")

        query = parse_qs(parsed.query)
        password = query.get("auth", [None])[0]
        sni = query.get("peer", [None])[0] or query.get("sni", [None])[0]
        remarks = unquote(parsed.fragment) if parsed.fragment else None

        logger.debug(f"hysteria节点解析成功: {host}:{port}")
        return Node(
            protocol="hysteria",
            host=host,
            port=port,
            password=password,
            tls=True,
            sni=sni,
            remarks=remarks,
        )
