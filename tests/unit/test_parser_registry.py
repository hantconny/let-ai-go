"""解析器注册表单元测试"""
import pytest
from src.parsers import get_parser, parse_uri, register_parser
from src.parsers.base import BaseParser
from src.models.node import Node


def test_get_parser_ss():
    parser = get_parser("ss://abc")
    assert parser is not None
    assert parser.__class__.__name__ == "ShadowsocksParser"


def test_get_parser_vmess():
    parser = get_parser("vmess://abc")
    assert parser is not None
    assert parser.__class__.__name__ == "VMessParser"


def test_get_parser_unknown():
    parser = get_parser("socks5://abc")
    assert parser is None


def test_parse_uri_unknown_protocol():
    with pytest.raises(ValueError, match="不支持的协议"):
        parse_uri("socks5://unknown.com:1080")


def test_register_custom_parser():
    class DummyParser(BaseParser):
        def can_parse(self, uri):
            return uri.startswith("dummy://")

        def parse(self, uri):
            return Node(protocol="dummy", host="h.com", port=1234)

    register_parser(DummyParser())
    parser = get_parser("dummy://test")
    assert parser is not None
