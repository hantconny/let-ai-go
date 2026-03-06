"""日志工具 - 基于loguru的结构化日志配置"""
import sys
import os
from pathlib import Path
from loguru import logger


def setup_logger(level: str = "INFO", log_file: str | None = None) -> None:
    """配置loguru日志记录器"""
    logger.remove()

    log_level = os.environ.get("SUBSCRIPTION_PARSER_LOG_LEVEL", level)

    # 控制台输出
    logger.add(
        sys.stderr,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}",
        colorize=True,
    )

    # 文件输出（DEBUG级别）
    if log_file is None:
        log_file = str(Path.home() / ".subscription-parser.log")

    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="7 days",
    )


# 默认初始化
setup_logger()
