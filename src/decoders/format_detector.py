"""格式检测器 - 多阶段检测管道，带回退链"""
from loguru import logger
from src.decoders import BaseDecoder
from src.decoders.base64_decoder import Base64Decoder, _extract_uris, _try_base64_decode, PROXY_PREFIXES
from src.decoders.yaml_decoder import YAMLDecoder


class FormatDetector:
    """订阅格式自动检测器，支持base64、YAML和混合格式"""

    def __init__(self):
        self._yaml_decoder = YAMLDecoder()
        self._base64_decoder = Base64Decoder()

    def detect_and_decode(self, content: str) -> tuple[str, list[str]]:
        """检测格式并解码内容

        Returns:
            (format_name, uri_list) 格式名称和URI列表元组

        格式检测顺序:
        1. 尝试YAML解析（最结构化）
        2. 尝试整体base64解码
        3. 尝试逐行base64解码（混合格式）
        4. 直接提取URI（纯文本格式）
        """
        # 步骤1: 尝试YAML
        if self._yaml_decoder.can_decode(content):
            logger.debug("检测到YAML格式")
            try:
                uris = self._yaml_decoder.decode(content)
                if uris:
                    return "yaml", uris
            except Exception as e:
                logger.warning(f"YAML解码失败，尝试其他格式: {e}")

        # 步骤2: 尝试整体base64解码
        decoded = _try_base64_decode(content.strip())
        if decoded:
            uris = _extract_uris(decoded)
            if uris:
                logger.debug(f"检测到base64格式，提取到 {len(uris)} 个URI")
                return "base64", uris

        # 步骤3: 尝试逐行处理（混合格式或纯文本）
        uris = []
        mixed = False
        for line in content.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if any(line.startswith(p) for p in PROXY_PREFIXES):
                uris.append(line)
                continue
            # 尝试逐行base64解码
            line_decoded = _try_base64_decode(line)
            if line_decoded:
                extracted = _extract_uris(line_decoded)
                if extracted:
                    uris.extend(extracted)
                    mixed = True

        if uris:
            format_name = "mixed" if mixed else "text"
            logger.debug(f"检测到{format_name}格式，提取到 {len(uris)} 个URI")
            return format_name, uris

        raise ValueError("无法识别订阅文件格式，已尝试: base64, yaml, mixed")
