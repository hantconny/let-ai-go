"""工具函数单元测试"""
import pytest
from src.utils.hash_generator import generate_node_id


def test_generate_node_id_format():
    node_id = generate_node_id("ss", "example.com", 8388)
    assert len(node_id) == 64
    assert all(c in "0123456789abcdef" for c in node_id)


def test_generate_node_id_deterministic():
    id1 = generate_node_id("vmess", "1.2.3.4", 443)
    id2 = generate_node_id("vmess", "1.2.3.4", 443)
    assert id1 == id2


def test_generate_node_id_unique():
    id1 = generate_node_id("ss", "example.com", 8388)
    id2 = generate_node_id("ss", "example.com", 8389)
    id3 = generate_node_id("vmess", "example.com", 8388)
    assert id1 != id2
    assert id1 != id3
    assert id2 != id3


def test_generate_node_id_canonical_format():
    # 确保使用规范格式: {protocol}://{host}:{port}
    id1 = generate_node_id("ss", "example.com", 443)
    import hashlib
    expected = hashlib.sha256("ss://example.com:443".encode()).hexdigest()
    assert id1 == expected
