"""解析器基类接口"""
from abc import ABC, abstractmethod
from src.models.node import Node


class BaseParser(ABC):
    """代理协议解析器基类"""

    @abstractmethod
    def parse(self, uri: str) -> Node:
        """解析协议URI，返回Node对象

        Args:
            uri: 协议URI字符串

        Returns:
            解析后的Node对象

        Raises:
            ValueError: URI格式无效时抛出
        """
        pass

    def can_parse(self, uri: str) -> bool:
        """检查是否能解析此URI"""
        return False
