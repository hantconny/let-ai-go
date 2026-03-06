"""Trojan (trojan://) 解析器"""
from urllib.parse import urlparse, parse_qs, unquote
from src.parsers.base import BaseParser
from src.models.node import Node
from loguru import logger


class TrojanParser(BaseParser):
    """Trojan (trojan://) 协议解析器"""

    def can_parse(self, uri: str) -> bool:
        return uri.startswith("trojan://")

    def parse(self, uri: str) -> Node:
        """解析trojan://格式URI

        格式: trojan://password@host:port?sni=xxx#remarks
        """
        if not uri.startswith("trojan://"):
            raise ValueError(f"无效的trojan URI: {uri}")

        parsed = urlparse(uri)
        password = unquote(parsed.username or "")
        host = parsed.hostname or ""
        port = parsed.port or 443

        if not host:
            raise ValueError("trojan URI缺少服务器地址")
        if not password:
            raise ValueError("trojan URI缺少密码")
        if not (1 <= port <= 65535):
            raise ValueError(f"端口超出范围: {port}")

        query = parse_qs(parsed.query)
        sni = query.get("sni", [None])[0] or query.get("peer", [None])[0]
        tls = True  # trojan默认使用TLS
        remarks = unquote(parsed.fragment) if parsed.fragment else None

        logger.debug(f"trojan节点解析成功: {host}:{port}")
        return Node(
            protocol="trojan",
            host=host,
            port=port,
            password=password,
            tls=tls,
            sni=sni,
            remarks=remarks,
        )
