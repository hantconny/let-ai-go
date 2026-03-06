"""SSR/Trojan/VLESS/Hysteria/Hysteria2解析器单元测试"""
import base64
import pytest
from src.parsers.ssr import ShadowsocksRParser
from src.parsers.trojan import TrojanParser
from src.parsers.vless import VLESSParser
from src.parsers.hysteria import HysteriaParser
from src.parsers.hysteria2 import Hysteria2Parser


# ─── SSR ───────────────────────────────────────────────────────────────────────

def _make_ssr_uri(host="ssr.example.com", port=443, auth="auth_sha1_v4",
                  cipher="aes-256-cfb", obfs="http_simple",
                  password="ssr_pass", remarks="Test-SSR") -> str:
    pw_b64 = base64.b64encode(password.encode()).decode()
    remarks_b64 = base64.b64encode(remarks.encode()).decode()
    body = f"{host}:{port}:{auth}:{cipher}:{obfs}:{pw_b64}/?remarks={remarks_b64}"
    return "ssr://" + base64.b64encode(body.encode()).decode()


class TestSSRParser:
    @pytest.fixture
    def parser(self):
        return ShadowsocksRParser()

    def test_can_parse(self, parser):
        assert parser.can_parse("ssr://abc") is True
        assert parser.can_parse("ss://abc") is False

    def test_parse_valid(self, parser):
        node = parser.parse(_make_ssr_uri())
        assert node.protocol == "ssr"
        assert node.host == "ssr.example.com"
        assert node.port == 443
        assert node.password == "ssr_pass"
        assert node.cipher == "aes-256-cfb"
        assert node.auth_protocol == "auth_sha1_v4"
        assert node.obfuscation == "http_simple"
        assert node.remarks == "Test-SSR"

    def test_parse_invalid_protocol(self, parser):
        with pytest.raises(ValueError, match="无效的ssr URI"):
            parser.parse("ss://invalid")

    def test_parse_invalid_base64(self, parser):
        with pytest.raises(ValueError):
            parser.parse("ssr://!!!invalid!!!")


# ─── Trojan ────────────────────────────────────────────────────────────────────

class TestTrojanParser:
    @pytest.fixture
    def parser(self):
        return TrojanParser()

    def test_can_parse(self, parser):
        assert parser.can_parse("trojan://abc") is True
        assert parser.can_parse("ss://abc") is False

    def test_parse_valid(self, parser):
        uri = "trojan://mypassword@trojan.example.com:443?sni=trojan.example.com#Test-Trojan"
        node = parser.parse(uri)
        assert node.protocol == "trojan"
        assert node.host == "trojan.example.com"
        assert node.port == 443
        assert node.password == "mypassword"
        assert node.tls is True
        assert node.sni == "trojan.example.com"
        assert node.remarks == "Test-Trojan"

    def test_parse_without_sni(self, parser):
        uri = "trojan://pass@host.com:443"
        node = parser.parse(uri)
        assert node.sni is None
        assert node.tls is True

    def test_parse_invalid_protocol(self, parser):
        with pytest.raises(ValueError, match="无效的trojan URI"):
            parser.parse("ss://invalid")

    def test_parse_missing_password(self, parser):
        with pytest.raises(ValueError, match="密码"):
            parser.parse("trojan://@host.com:443")


# ─── VLESS ─────────────────────────────────────────────────────────────────────

class TestVLESSParser:
    @pytest.fixture
    def parser(self):
        return VLESSParser()

    def test_can_parse(self, parser):
        assert parser.can_parse("vless://abc") is True
        assert parser.can_parse("vmess://abc") is False

    def test_parse_valid(self, parser):
        uri = "vless://87654321-4321-4321-4321-210987654321@vless.example.com:443?type=tcp&security=tls&sni=vless.example.com#Test-VLESS"
        node = parser.parse(uri)
        assert node.protocol == "vless"
        assert node.host == "vless.example.com"
        assert node.port == 443
        assert node.uuid == "87654321-4321-4321-4321-210987654321"
        assert node.tls is True
        assert node.transport == "tcp"
        assert node.sni == "vless.example.com"
        assert node.remarks == "Test-VLESS"

    def test_parse_no_tls(self, parser):
        uri = "vless://uuid@host.com:443?type=tcp&security=none"
        node = parser.parse(uri)
        assert node.tls is False

    def test_parse_invalid_protocol(self, parser):
        with pytest.raises(ValueError, match="无效的vless URI"):
            parser.parse("vmess://invalid")

    def test_parse_missing_uuid(self, parser):
        with pytest.raises(ValueError, match="uuid"):
            parser.parse("vless://@host.com:443")


# ─── Hysteria ──────────────────────────────────────────────────────────────────

class TestHysteriaParser:
    @pytest.fixture
    def parser(self):
        return HysteriaParser()

    def test_can_parse(self, parser):
        assert parser.can_parse("hysteria://abc") is True
        assert parser.can_parse("hysteria2://abc") is False

    def test_parse_valid(self, parser):
        uri = "hysteria://hysteria.example.com:443?auth=hysteria_pass&peer=hysteria.example.com#Test-Hysteria"
        node = parser.parse(uri)
        assert node.protocol == "hysteria"
        assert node.host == "hysteria.example.com"
        assert node.port == 443
        assert node.password == "hysteria_pass"
        assert node.tls is True
        assert node.sni == "hysteria.example.com"
        assert node.remarks == "Test-Hysteria"

    def test_parse_invalid_protocol(self, parser):
        with pytest.raises(ValueError, match="无效的hysteria URI"):
            parser.parse("hysteria2://invalid")


# ─── Hysteria2 ─────────────────────────────────────────────────────────────────

class TestHysteria2Parser:
    @pytest.fixture
    def parser(self):
        return Hysteria2Parser()

    def test_can_parse(self, parser):
        assert parser.can_parse("hysteria2://abc") is True
        assert parser.can_parse("hysteria://abc") is False

    def test_parse_valid(self, parser):
        uri = "hysteria2://hysteria2_pass@hysteria2.example.com:443?sni=hysteria2.example.com#Test-Hysteria2"
        node = parser.parse(uri)
        assert node.protocol == "hysteria2"
        assert node.host == "hysteria2.example.com"
        assert node.port == 443
        assert node.password == "hysteria2_pass"
        assert node.tls is True
        assert node.sni == "hysteria2.example.com"
        assert node.remarks == "Test-Hysteria2"

    def test_parse_no_password(self, parser):
        uri = "hysteria2://hysteria2.example.com:443?sni=sni.com"
        node = parser.parse(uri)
        assert node.password is None

    def test_parse_invalid_protocol(self, parser):
        with pytest.raises(ValueError, match="无效的hysteria2 URI"):
            parser.parse("hysteria://invalid")
