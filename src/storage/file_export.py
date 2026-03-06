"""文件导出模块 - 支持JSON和CSV格式"""
import csv
import json
import time
from pathlib import Path
from loguru import logger
from src.models import ParseResult
from src.models.node import Node
from src.models.subscription import Subscription


# CSV字段顺序
CSV_FIELDS = [
    "node_id", "protocol", "host", "port", "tls", "sni",
    "uuid", "password", "cipher", "transport", "network",
    "auth_protocol", "obfuscation", "remarks", "source_id", "parsed_at",
]

MAX_RETRIES = 3


def export_json(result: ParseResult, output_path: str) -> None:
    """导出解析结果为JSON格式，带重试机制"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            data = result.to_dict()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON导出成功: {output_path}")
            return
        except OSError as e:
            logger.warning(f"JSON导出失败 ({attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
            else:
                raise


def export_csv(result: ParseResult, output_path: str) -> None:
    """导出解析结果为CSV格式，带重试机制"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
                writer.writeheader()
                for node in result.nodes:
                    row = node.to_dict()
                    # 将None替换为空字符串
                    row = {k: ("" if v is None else v) for k, v in row.items()}
                    writer.writerow(row)
            logger.info(f"CSV导出成功: {output_path}")
            return
        except OSError as e:
            logger.warning(f"CSV导出失败 ({attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)
            else:
                raise


def export_nodes_json(nodes: list[Node], subscription: Subscription, output_path: str) -> None:
    """从节点列表直接导出JSON（用于export命令）"""
    from datetime import datetime, timezone
    result = ParseResult(
        subscription=subscription,
        nodes=nodes,
        export_format="json",
        exported_at=datetime.now(timezone.utc),
    )
    export_json(result, output_path)


def export_nodes_csv(nodes: list[Node], subscription: Subscription, output_path: str) -> None:
    """从节点列表直接导出CSV（用于export命令）"""
    from datetime import datetime, timezone
    result = ParseResult(
        subscription=subscription,
        nodes=nodes,
        export_format="csv",
        exported_at=datetime.now(timezone.utc),
    )
    export_csv(result, output_path)
