"""YAML解码器 - 解码YAML格式的订阅内容（Clash格式）"""
import base64
import json
import yaml
from src.decoders import BaseDecoder
from loguru import logger


class YAMLDecoder(BaseDecoder):
    """YAML/Clash格式订阅解码器"""

    def can_decode(self, content: str) -> bool:
        """检查内容是否为有效YAML格式"""
        try:
            data = yaml.safe_load(content)
            return isinstance(data, dict) and "proxies" in data
        except Exception:
            return False

    def decode(self, content: str) -> list[str]:
        """解码YAML订阅内容，将proxies转换为URI列表"""
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML解析失败: {e}")

        if not isinstance(data, dict):
            raise ValueError("YAML内容不是字典格式")

        proxies = data.get("proxies", [])
        if not proxies:
            raise ValueError("YAML中没有proxies字段")

        uris = []
        for proxy in proxies:
            uri = self._proxy_to_uri(proxy)
            if uri:
                uris.append(uri)

        logger.debug(f"YAML解码成功，提取到 {len(uris)} 个URI")
        return uris

    def _proxy_to_uri(self, proxy: dict) -> str | None:
        """将Clash代理配置转换为URI格式"""
        try:
            proxy_type = proxy.get("type", "").lower()
            name = proxy.get("name", "")
            server = proxy.get("server", "")
            port = proxy.get("port", 0)

            if not server or not port:
                return None

            if proxy_type == "ss":
                password = proxy.get("password", "")
                cipher = proxy.get("cipher", "aes-256-gcm")
                userinfo = base64.b64encode(f"{cipher}:{password}".encode()).decode()
                return f"ss://{userinfo}@{server}:{port}#{name}"

            elif proxy_type == "vmess":
                config = {
                    "v": "2",
                    "ps": name,
                    "add": server,
                    "port": str(port),
                    "id": proxy.get("uuid", ""),
                    "aid": str(proxy.get("alterId", 0)),
                    "net": proxy.get("network", "tcp"),
                    "type": "none",
                    "tls": "tls" if proxy.get("tls", False) else "",
                    "sni": proxy.get("servername", ""),
                    "scy": proxy.get("cipher", "auto"),
                }
                encoded = base64.b64encode(json.dumps(config).encode()).decode()
                return f"vmess://{encoded}"

            elif proxy_type == "trojan":
                password = proxy.get("password", "")
                sni = proxy.get("sni", server)
                return f"trojan://{password}@{server}:{port}?sni={sni}#{name}"

            elif proxy_type == "vless":
                uuid = proxy.get("uuid", "")
                network = proxy.get("network", "tcp")
                tls_type = "tls" if proxy.get("tls", False) else "none"
                sni = proxy.get("servername", "")
                return f"vless://{uuid}@{server}:{port}?type={network}&security={tls_type}&sni={sni}#{name}"

            elif proxy_type in ("hysteria", "hysteria2"):
                auth = proxy.get("auth", proxy.get("password", ""))
                sni = proxy.get("sni", server)
                return f"{proxy_type}://{server}:{port}?auth={auth}&peer={sni}#{name}"

            return None
        except Exception as e:
            logger.warning(f"代理配置转换失败: {e}, 配置: {proxy}")
            return None
