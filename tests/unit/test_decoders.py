"""格式解码器单元测试"""
import base64
import pytest
from src.decoders.base64_decoder import Base64Decoder
from src.decoders.yaml_decoder import YAMLDecoder
from src.decoders.format_detector import FormatDetector


SS_URI = "ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ=@example.com:8388#Test"
VMESS_URI = "vmess://eyJ2IjogIjIiLCAiYWRkIjogImguY29tIiwgInBvcnQiOiAiNDQzIiwgImlkIjogInV1aWQifQ=="


# ─── Base64Decoder ─────────────────────────────────────────────────────────────

class TestBase64Decoder:
    @pytest.fixture
    def decoder(self):
        return Base64Decoder()

    def _encode(self, text: str) -> str:
        return base64.b64encode(text.encode()).decode()

    def test_can_decode_valid_base64(self, decoder):
        content = self._encode(f"{SS_URI}\n{VMESS_URI}")
        assert decoder.can_decode(content) is True

    def test_cannot_decode_plain_uri(self, decoder):
        assert decoder.can_decode(SS_URI) is False

    def test_cannot_decode_random_text(self, decoder):
        assert decoder.can_decode("hello world this is plain text") is False

    def test_decode_single_uri(self, decoder):
        content = self._encode(SS_URI)
        uris = decoder.decode(content)
        assert len(uris) == 1
        assert uris[0] == SS_URI

    def test_decode_multiple_uris(self, decoder):
        content = self._encode(f"{SS_URI}\n{VMESS_URI}")
        uris = decoder.decode(content)
        assert len(uris) == 2

    def test_decode_invalid_base64(self, decoder):
        with pytest.raises(ValueError, match="解码失败"):
            decoder.decode("!!!not_base64!!!")


# ─── YAMLDecoder ───────────────────────────────────────────────────────────────

YAML_CONTENT = """
proxies:
  - name: Test-SS
    type: ss
    server: yaml.example.com
    port: 8388
    cipher: aes-256-gcm
    password: yaml_pass
  - name: Test-VMess
    type: vmess
    server: vmess.example.com
    port: 443
    uuid: 12345678-1234-1234-1234-123456789012
    alterId: 0
    cipher: auto
    tls: true
    network: ws
"""


class TestYAMLDecoder:
    @pytest.fixture
    def decoder(self):
        return YAMLDecoder()

    def test_can_decode_valid_yaml(self, decoder):
        assert decoder.can_decode(YAML_CONTENT) is True

    def test_cannot_decode_plain_text(self, decoder):
        assert decoder.can_decode(SS_URI) is False

    def test_cannot_decode_yaml_without_proxies(self, decoder):
        assert decoder.can_decode("key: value\nother: data") is False

    def test_decode_ss_proxy(self, decoder):
        uris = decoder.decode(YAML_CONTENT)
        ss_uris = [u for u in uris if u.startswith("ss://")]
        assert len(ss_uris) == 1

    def test_decode_vmess_proxy(self, decoder):
        uris = decoder.decode(YAML_CONTENT)
        vmess_uris = [u for u in uris if u.startswith("vmess://")]
        assert len(vmess_uris) == 1

    def test_decode_invalid_yaml(self, decoder):
        with pytest.raises(ValueError, match="YAML解析失败"):
            decoder.decode("key: [unclosed bracket")

    def test_decode_empty_proxies(self, decoder):
        with pytest.raises(ValueError, match="没有proxies"):
            decoder.decode("proxies: []")


# ─── FormatDetector ────────────────────────────────────────────────────────────

class TestFormatDetector:
    @pytest.fixture
    def detector(self):
        return FormatDetector()

    def test_detect_yaml(self, detector):
        fmt, uris = detector.detect_and_decode(YAML_CONTENT)
        assert fmt == "yaml"
        assert len(uris) >= 1

    def test_detect_base64(self, detector):
        content = base64.b64encode(f"{SS_URI}\n{VMESS_URI}".encode()).decode()
        fmt, uris = detector.detect_and_decode(content)
        assert fmt == "base64"
        assert len(uris) == 2

    def test_detect_plain_text(self, detector):
        content = f"{SS_URI}\n{VMESS_URI}\ntrojan://pass@h.com:443"
        fmt, uris = detector.detect_and_decode(content)
        assert fmt == "text"
        assert len(uris) == 3

    def test_detect_unrecognized_format(self, detector):
        with pytest.raises(ValueError, match="无法识别"):
            detector.detect_and_decode("this is just random plain text with no uris")

    def test_detect_from_file(self, detector):
        import pathlib
        fixture = pathlib.Path("tests/fixtures/sample_text.txt").read_text()
        fmt, uris = detector.detect_and_decode(fixture)
        assert len(uris) == 7
        protocols = {u.split("://")[0] for u in uris}
        assert "ss" in protocols
        assert "vmess" in protocols
