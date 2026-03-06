"""数据模型包 - 包含ParseResult模型"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from src.models.node import Node
from src.models.subscription import Subscription


@dataclass
class ParseResult:
    """解析结果模型，包含订阅元数据和节点列表"""

    subscription: Subscription
    nodes: list[Node]
    export_format: str = "json"
    exported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """将解析结果转换为字典"""
        return {
            "subscription": self.subscription.to_dict(),
            "nodes": [node.to_dict() for node in self.nodes],
            "export_format": self.export_format,
            "exported_at": self.exported_at.isoformat(),
        }
