"""Base64解码器 - 解码base64编码的订阅内容"""
import base64
import re
from src.decoders import BaseDecoder
from loguru import logger

# 代理协议URI前缀
PROXY_PREFIXES = ("ss://", "ssr://", "trojan://", "vmess://", "vless://", "hysteria://", "hysteria2://")


def _extract_uris(text: str) -> list[str]:
    """从文本中提取代理URI"""
    lines = text.strip().splitlines()
    uris = []
    for line in lines:
        line = line.strip()
        if any(line.startswith(p) for p in PROXY_PREFIXES):
            uris.append(line)
    return uris


def _try_base64_decode(content: str) -> str | None:
    """尝试base64解码，失败返回None"""
    content = content.strip()
    # 补全base64填充
    padding = 4 - len(content) % 4
    if padding != 4:
        content += "=" * padding
    try:
        decoded = base64.b64decode(content).decode("utf-8", errors="replace")
        return decoded
    except Exception:
        return None


class Base64Decoder(BaseDecoder):
    """Base64格式订阅解码器"""

    def can_decode(self, content: str) -> bool:
        """检查内容是否为有效base64编码"""
        content = content.strip()
        # 检查是否包含非base64字符（代理URI前缀除外）
        if any(content.startswith(p) for p in PROXY_PREFIXES):
            return False
        decoded = _try_base64_decode(content)
        if decoded is None:
            return False
        uris = _extract_uris(decoded)
        return len(uris) > 0

    def decode(self, content: str) -> list[str]:
        """解码base64订阅内容，返回URI列表"""
        decoded = _try_base64_decode(content.strip())
        if decoded is None:
            raise ValueError("Base64解码失败")

        uris = _extract_uris(decoded)
        if not uris:
            # 尝试逐行解码（混合格式）
            uris = self._decode_mixed(content)

        logger.debug(f"Base64解码成功，提取到 {len(uris)} 个URI")
        return uris

    def _decode_mixed(self, content: str) -> list[str]:
        """尝试逐行base64解码（混合格式）"""
        uris = []
        for line in content.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if any(line.startswith(p) for p in PROXY_PREFIXES):
                uris.append(line)
                continue
            decoded = _try_base64_decode(line)
            if decoded:
                extracted = _extract_uris(decoded)
                uris.extend(extracted)
        return uris
