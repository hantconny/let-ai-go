"""Shadowsocks解析器单元测试"""
import pytest
from src.parsers.ss import ShadowsocksParser


@pytest.fixture
def parser():
    return ShadowsocksParser()


def test_can_parse_ss_uri(parser):
    assert parser.can_parse("ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ=@example.com:8388") is True


def test_cannot_parse_other_uri(parser):
    assert parser.can_parse("vmess://abc") is False
    assert parser.can_parse("trojan://abc") is False


def test_parse_valid_ss_uri(parser):
    # base64("aes-256-gcm:password") = "YWVzLTI1Ni1nY206cGFzc3dvcmQ="
    uri = "ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ=@example.com:8388#MyNode"
    node = parser.parse(uri)
    assert node.protocol == "ss"
    assert node.host == "example.com"
    assert node.port == 8388
    assert node.cipher == "aes-256-gcm"
    assert node.password == "password"
    assert node.remarks == "MyNode"


def test_parse_ss_uri_without_remarks(parser):
    uri = "ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ=@example.com:8388"
    node = parser.parse(uri)
    assert node.remarks is None


def test_parse_ss_uri_with_encoded_remarks(parser):
    uri = "ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ=@example.com:8388#My%20Node"
    node = parser.parse(uri)
    assert node.remarks == "My Node"


def test_parse_invalid_protocol(parser):
    with pytest.raises(ValueError, match="无效的ss URI"):
        parser.parse("vmess://invalid")


def test_parse_missing_at_separator(parser):
    with pytest.raises(ValueError, match="@分隔符"):
        parser.parse("ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ=example.com:8388")


def test_parse_invalid_base64_userinfo(parser):
    with pytest.raises(ValueError, match="解码失败"):
        parser.parse("ss://not_valid_base64!@example.com:8388")


def test_parse_missing_port(parser):
    import base64
    userinfo = base64.b64encode(b"aes-256-gcm:password").decode()
    with pytest.raises(ValueError, match="端口"):
        parser.parse(f"ss://{userinfo}@example.com")
