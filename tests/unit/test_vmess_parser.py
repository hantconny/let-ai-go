"""VMess解析器单元测试"""
import base64
import json
import pytest
from src.parsers.vmess import VMessParser


@pytest.fixture
def parser():
    return VMessParser()


def _make_vmess_uri(config: dict) -> str:
    encoded = base64.b64encode(json.dumps(config).encode()).decode()
    return f"vmess://{encoded}"


@pytest.fixture
def valid_config():
    return {
        "v": "2", "ps": "Test Node", "add": "vmess.example.com",
        "port": "443", "id": "12345678-1234-1234-1234-123456789012",
        "aid": "0", "net": "ws", "type": "none",
        "tls": "tls", "sni": "vmess.example.com", "scy": "auto",
    }


def test_can_parse_vmess_uri(parser):
    assert parser.can_parse("vmess://abc") is True


def test_cannot_parse_other_uri(parser):
    assert parser.can_parse("ss://abc") is False


def test_parse_valid_vmess(parser, valid_config):
    node = parser.parse(_make_vmess_uri(valid_config))
    assert node.protocol == "vmess"
    assert node.host == "vmess.example.com"
    assert node.port == 443
    assert node.uuid == "12345678-1234-1234-1234-123456789012"
    assert node.cipher == "auto"
    assert node.transport == "ws"
    assert node.tls is True
    assert node.sni == "vmess.example.com"
    assert node.remarks == "Test Node"


def test_parse_vmess_tls_false(parser, valid_config):
    valid_config["tls"] = ""
    node = parser.parse(_make_vmess_uri(valid_config))
    assert node.tls is False


def test_parse_vmess_integer_port(parser, valid_config):
    valid_config["port"] = 8080
    node = parser.parse(_make_vmess_uri(valid_config))
    assert node.port == 8080


def test_parse_missing_host(parser):
    config = {"v": "2", "add": "", "port": "443", "id": "uuid"}
    with pytest.raises(ValueError, match="服务器地址"):
        parser.parse(_make_vmess_uri(config))


def test_parse_missing_uuid(parser):
    config = {"v": "2", "add": "host.com", "port": "443", "id": ""}
    with pytest.raises(ValueError, match="uuid"):
        parser.parse(_make_vmess_uri(config))


def test_parse_invalid_base64(parser):
    with pytest.raises(ValueError, match="解码失败"):
        parser.parse("vmess://not!valid!base64!!!")


def test_parse_invalid_protocol(parser):
    with pytest.raises(ValueError, match="无效的vmess URI"):
        parser.parse("ss://something")
