"""文件导出单元测试"""
import csv
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone
from src.models.node import Node
from src.models.subscription import Subscription
from src.models import ParseResult
from src.storage.file_export import export_json, export_csv


@pytest.fixture
def sample_subscription():
    return Subscription(
        source_id="test_sub",
        file_path="/data/test_sub.txt",
        format="base64",
        total_nodes=2,
        successful_nodes=2,
        failed_nodes=0,
        parsed_at=datetime(2026, 3, 6, 10, 0, 0, tzinfo=timezone.utc),
        duration_ms=100,
    )


@pytest.fixture
def sample_nodes():
    return [
        Node(protocol="ss", host="example.com", port=8388,
             password="pass", cipher="aes-256-gcm", remarks="Node 1",
             source_id="test_sub"),
        Node(protocol="vmess", host="vmess.example.com", port=443,
             uuid="12345678-1234-1234-1234-123456789012", cipher="auto",
             tls=True, sni="vmess.example.com", remarks="Node 2",
             source_id="test_sub"),
    ]


@pytest.fixture
def parse_result(sample_subscription, sample_nodes):
    return ParseResult(
        subscription=sample_subscription,
        nodes=sample_nodes,
        export_format="json",
    )


class TestJSONExport:
    def test_export_creates_file(self, tmp_path, parse_result):
        output = str(tmp_path / "output.json")
        export_json(parse_result, output)
        assert Path(output).exists()

    def test_export_valid_json(self, tmp_path, parse_result):
        output = str(tmp_path / "output.json")
        export_json(parse_result, output)
        with open(output) as f:
            data = json.load(f)
        assert "subscription" in data
        assert "nodes" in data
        assert "export_format" in data
        assert "exported_at" in data

    def test_export_correct_node_count(self, tmp_path, parse_result):
        output = str(tmp_path / "output.json")
        export_json(parse_result, output)
        with open(output) as f:
            data = json.load(f)
        assert len(data["nodes"]) == 2

    def test_export_node_fields(self, tmp_path, parse_result):
        output = str(tmp_path / "output.json")
        export_json(parse_result, output)
        with open(output) as f:
            data = json.load(f)
        node = data["nodes"][0]
        assert "node_id" in node
        assert "protocol" in node
        assert "host" in node
        assert "port" in node

    def test_export_creates_parent_dirs(self, tmp_path, parse_result):
        output = str(tmp_path / "nested" / "dir" / "output.json")
        export_json(parse_result, output)
        assert Path(output).exists()


class TestCSVExport:
    def test_export_creates_file(self, tmp_path, parse_result):
        output = str(tmp_path / "output.csv")
        export_csv(parse_result, output)
        assert Path(output).exists()

    def test_export_has_header(self, tmp_path, parse_result):
        output = str(tmp_path / "output.csv")
        export_csv(parse_result, output)
        with open(output, newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert "node_id" in header
        assert "protocol" in header
        assert "host" in header
        assert "port" in header

    def test_export_correct_row_count(self, tmp_path, parse_result):
        output = str(tmp_path / "output.csv")
        export_csv(parse_result, output)
        with open(output, newline="") as f:
            rows = list(csv.reader(f))
        # header + 2 nodes
        assert len(rows) == 3

    def test_export_none_as_empty_string(self, tmp_path, parse_result):
        output = str(tmp_path / "output.csv")
        export_csv(parse_result, output)
        with open(output, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        # ss节点没有uuid，应为空字符串
        ss_row = next(r for r in rows if r["protocol"] == "ss")
        assert ss_row["uuid"] == ""
