"""订阅元数据模型"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Subscription:
    """订阅文件元数据"""

    source_id: str
    file_path: str
    format: str
    total_nodes: int
    successful_nodes: int
    failed_nodes: int
    parsed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """将订阅元数据转换为字典"""
        return {
            "source_id": self.source_id,
            "file_path": self.file_path,
            "format": self.format,
            "total_nodes": self.total_nodes,
            "successful_nodes": self.successful_nodes,
            "failed_nodes": self.failed_nodes,
            "parsed_at": self.parsed_at.isoformat(),
            "duration_ms": self.duration_ms,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Subscription":
        """从字典创建订阅对象"""
        parsed_at = data.get("parsed_at")
        if isinstance(parsed_at, str):
            parsed_at = datetime.fromisoformat(parsed_at)
        elif parsed_at is None:
            parsed_at = datetime.now(timezone.utc)

        errors = data.get("errors", [])
        if isinstance(errors, str):
            import json
            try:
                errors = json.loads(errors)
            except Exception:
                errors = [errors] if errors else []

        return cls(
            source_id=data["source_id"],
            file_path=data["file_path"],
            format=data["format"],
            total_nodes=int(data["total_nodes"]),
            successful_nodes=int(data["successful_nodes"]),
            failed_nodes=int(data["failed_nodes"]),
            parsed_at=parsed_at,
            duration_ms=int(data.get("duration_ms", 0)),
            errors=errors,
        )
