"""Node模型单元测试"""
import pytest
from datetime import datetime, timezone
from src.models.node import Node


def test_node_auto_generates_node_id():
    node = Node(protocol="ss", host="example.com", port=8388)
    assert node.node_id is not None
    assert len(node.node_id) == 64


def test_node_same_id_for_same_attributes():
    node1 = Node(protocol="ss", host="example.com", port=8388)
    node2 = Node(protocol="ss", host="example.com", port=8388)
    assert node1.node_id == node2.node_id


def test_node_different_id_for_different_port():
    node1 = Node(protocol="ss", host="example.com", port=8388)
    node2 = Node(protocol="ss", host="example.com", port=8389)
    assert node1.node_id != node2.node_id


def test_node_to_dict():
    node = Node(
        protocol="ss",
        host="example.com",
        port=8388,
        password="pass",
        cipher="aes-256-gcm",
        remarks="Test",
    )
    d = node.to_dict()
    assert d["protocol"] == "ss"
    assert d["host"] == "example.com"
    assert d["port"] == 8388
    assert d["password"] == "pass"
    assert d["cipher"] == "aes-256-gcm"
    assert d["remarks"] == "Test"
    assert d["node_id"] == node.node_id


def test_node_to_dict_none_fields():
    node = Node(protocol="ss", host="example.com", port=8388)
    d = node.to_dict()
    assert d["uuid"] is None
    assert d["password"] is None
    assert d["sni"] is None


def test_node_from_dict_roundtrip():
    node = Node(
        protocol="vmess",
        host="1.2.3.4",
        port=443,
        uuid="12345678-1234-1234-1234-123456789012",
        cipher="auto",
        tls=True,
        sni="example.com",
        remarks="Test VMess",
        source_id="my_sub",
    )
    d = node.to_dict()
    restored = Node.from_dict(d)
    assert restored.protocol == node.protocol
    assert restored.host == node.host
    assert restored.port == node.port
    assert restored.uuid == node.uuid
    assert restored.tls == node.tls
    assert restored.sni == node.sni
    assert restored.node_id == node.node_id


def test_node_from_dict_bool_conversion():
    data = {
        "protocol": "trojan", "host": "h.com", "port": "443",
        "tls": "true", "password": "pw",
    }
    node = Node.from_dict(data)
    assert node.tls is True
    assert node.port == 443


def test_node_defaults():
    node = Node(protocol="ss", host="h.com", port=80)
    assert node.tls is False
    assert node.source_id is None
    assert isinstance(node.parsed_at, datetime)
