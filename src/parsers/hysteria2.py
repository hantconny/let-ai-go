"""Hysteria2 (hysteria2://) 解析器"""
from urllib.parse import urlparse, parse_qs, unquote
from src.parsers.base import BaseParser
from src.models.node import Node
from loguru import logger


class Hysteria2Parser(BaseParser):
    """Hysteria2 (hysteria2://) 协议解析器"""

    def can_parse(self, uri: str) -> bool:
        return uri.startswith("hysteria2://")

    def parse(self, uri: str) -> Node:
        """解析hysteria2://格式URI

        格式: hysteria2://password@host:port?sni=xxx#remarks
        """
        if not uri.startswith("hysteria2://"):
            raise ValueError(f"无效的hysteria2 URI: {uri}")

        parsed = urlparse(uri)
        host = parsed.hostname or ""
        port = parsed.port or 443
        password = unquote(parsed.username or "") or None

        if not host:
            raise ValueError("hysteria2 URI缺少服务器地址")
        if not (1 <= port <= 65535):
            raise ValueError(f"端口超出范围: {port}")

        query = parse_qs(parsed.query)
        sni = query.get("sni", [None])[0] or query.get("peer", [None])[0]
        remarks = unquote(parsed.fragment) if parsed.fragment else None

        logger.debug(f"hysteria2节点解析成功: {host}:{port}")
        return Node(
            protocol="hysteria2",
            host=host,
            port=port,
            password=password,
            tls=True,
            sni=sni,
            remarks=remarks,
        )
