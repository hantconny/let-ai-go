"""SHA256哈希生成器 - 用于生成节点唯一ID"""
import hashlib


def generate_node_id(protocol: str, host: str, port: int) -> str:
    """根据协议、主机和端口生成SHA256哈希作为节点ID

    哈希输入格式: {protocol}://{host}:{port}
    """
    canonical = f"{protocol}://{host}:{port}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
