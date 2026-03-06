"""解析器注册表 - 所有协议解析器的注册和选择"""
from src.parsers.base import BaseParser
from src.parsers.ss import ShadowsocksParser
from src.parsers.vmess import VMessParser
from src.parsers.ssr import ShadowsocksRParser
from src.parsers.trojan import TrojanParser
from src.parsers.vless import VLESSParser
from src.parsers.hysteria import HysteriaParser
from src.parsers.hysteria2 import Hysteria2Parser
from loguru import logger

# 全局解析器注册表 - 按照协议注册顺序
_PARSERS: list[BaseParser] = [
    ShadowsocksParser(),
    VMessParser(),
    ShadowsocksRParser(),
    TrojanParser(),
    VLESSParser(),
    HysteriaParser(),
    Hysteria2Parser(),
]


def register_parser(parser: BaseParser) -> None:
    """注册新的协议解析器"""
    _PARSERS.append(parser)


def get_parser(uri: str) -> BaseParser | None:
    """根据URI获取对应的解析器"""
    for parser in _PARSERS:
        if parser.can_parse(uri):
            return parser
    return None


def parse_uri(uri: str):
    """解析单个URI，失败时抛出异常"""
    parser = get_parser(uri)
    if parser is None:
        raise ValueError(f"不支持的协议URI: {uri[:50]}")
    return parser.parse(uri)
