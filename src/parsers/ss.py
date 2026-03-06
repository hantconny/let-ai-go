"""Shadowsocks (ss://) 解析器"""
import base64
from urllib.parse import unquote, urlparse
from src.parsers.base import BaseParser
from src.models.node import Node
from loguru import logger


class ShadowsocksParser(BaseParser):
    """Shadowsocks (ss://) 协议解析器"""

    def can_parse(self, uri: str) -> bool:
        return uri.startswith("ss://")

    def parse(self, uri: str) -> Node:
        """解析ss://格式URI

        格式: ss://base64(cipher:password)@host:port#remarks
        """
        if not uri.startswith("ss://"):
            raise ValueError(f"无效的ss URI: {uri}")

        # 分离remarks
        remarks = None
        if "#" in uri:
            uri, remarks_encoded = uri.split("#", 1)
            remarks = unquote(remarks_encoded)

        body = uri[5:]  # 去除 ss://

        # 分离用户信息和服务器
        if "@" not in body:
            raise ValueError("ss URI中缺少@分隔符")

        userinfo, server = body.rsplit("@", 1)

        # 解码用户信息
        try:
            # 补全base64填充
            padding = 4 - len(userinfo) % 4
            if padding != 4:
                userinfo += "=" * padding
            decoded_userinfo = base64.b64decode(userinfo).decode("utf-8")
            if ":" not in decoded_userinfo:
                raise ValueError("用户信息格式无效")
            cipher, password = decoded_userinfo.split(":", 1)
        except Exception as e:
            raise ValueError(f"ss用户信息解码失败: {e}")

        # 解析服务器地址和端口
        if ":" not in server:
            raise ValueError("ss URI中缺少端口")

        # 处理IPv6地址
        if server.startswith("["):
            host, port_str = server.rsplit(":", 1)
            host = host.strip("[]")
        else:
            host, port_str = server.rsplit(":", 1)

        try:
            port = int(port_str)
        except ValueError:
            raise ValueError(f"无效的端口: {port_str}")

        if not (1 <= port <= 65535):
            raise ValueError(f"端口超出范围: {port}")

        logger.debug(f"ss节点解析成功: {host}:{port}")
        return Node(
            protocol="ss",
            host=host,
            port=port,
            password=password,
            cipher=cipher,
            remarks=remarks,
        )
