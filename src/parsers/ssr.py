"""ShadowsocksR (ssr://) 解析器"""
import base64
from urllib.parse import unquote
from src.parsers.base import BaseParser
from src.models.node import Node
from loguru import logger


def _safe_b64decode(s: str) -> str:
    """安全的base64解码，自动补全填充"""
    s = s.strip()
    # 替换URL安全字符
    s = s.replace("-", "+").replace("_", "/")
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.b64decode(s).decode("utf-8", errors="replace")


class ShadowsocksRParser(BaseParser):
    """ShadowsocksR (ssr://) 协议解析器"""

    def can_parse(self, uri: str) -> bool:
        return uri.startswith("ssr://")

    def parse(self, uri: str) -> Node:
        """解析ssr://格式URI

        格式: ssr://base64(host:port:auth:cipher:obfs:base64(password)/?params)
        """
        if not uri.startswith("ssr://"):
            raise ValueError(f"无效的ssr URI: {uri}")

        encoded = uri[6:]  # 去除 ssr://
        try:
            decoded = _safe_b64decode(encoded)
        except Exception as e:
            raise ValueError(f"ssr URI解码失败: {e}")

        # 分离参数
        params_str = ""
        if "/?" in decoded:
            main_part, params_str = decoded.split("/?", 1)
        elif "/" in decoded:
            main_part = decoded.rsplit("/", 1)[0]
        else:
            main_part = decoded

        # 解析主要字段: host:port:auth:cipher:obfs:base64(password)
        parts = main_part.split(":")
        if len(parts) < 6:
            raise ValueError(f"ssr URI字段不足: {main_part}")

        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            raise ValueError(f"无效的端口: {parts[1]}")

        auth_protocol = parts[2]
        cipher = parts[3]
        obfuscation = parts[4]
        password_b64 = parts[5]

        try:
            password = _safe_b64decode(password_b64)
        except Exception as e:
            raise ValueError(f"ssr密码解码失败: {e}")

        # 解析可选参数
        remarks = None
        if params_str:
            for param in params_str.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    if key == "remarks":
                        try:
                            remarks = _safe_b64decode(value)
                        except Exception:
                            remarks = unquote(value)

        if not (1 <= port <= 65535):
            raise ValueError(f"端口超出范围: {port}")

        logger.debug(f"ssr节点解析成功: {host}:{port}")
        return Node(
            protocol="ssr",
            host=host,
            port=port,
            password=password,
            cipher=cipher,
            auth_protocol=auth_protocol,
            obfuscation=obfuscation,
            remarks=remarks,
        )
