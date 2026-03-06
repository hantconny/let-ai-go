"""解码器包 - 格式检测和解码基础接口"""
from abc import ABC, abstractmethod


class BaseDecoder(ABC):
    """订阅格式解码器基类"""

    @abstractmethod
    def decode(self, content: str) -> list[str]:
        """解码订阅内容，返回URI列表

        Args:
            content: 原始订阅文件内容

        Returns:
            解码后的代理URI列表

        Raises:
            ValueError: 内容格式不支持时抛出
        """
        pass

    @abstractmethod
    def can_decode(self, content: str) -> bool:
        """检查是否能解码此内容"""
        pass
