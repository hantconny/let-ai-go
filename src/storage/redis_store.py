"""Redis存储管理器 - 连接池和节点存储操作"""
import json
import time
from typing import Optional
import redis
from redis import ConnectionPool, Redis
from loguru import logger
from src.models.node import Node
from src.models.subscription import Subscription

# Redis键的TTL: 7天（秒）
TTL_SECONDS = 7 * 24 * 3600


class RedisStore:
    """Redis存储管理器，支持连接池和重试机制"""

    def __init__(self, url: str = "redis://localhost:6379/0", max_retries: int = 3):
        """初始化Redis连接池"""
        self._url = url
        self._max_retries = max_retries
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None

    def connect(self) -> None:
        """建立Redis连接，带重试机制"""
        for attempt in range(1, self._max_retries + 1):
            try:
                self._pool = ConnectionPool.from_url(
                    self._url,
                    decode_responses=True,
                    max_connections=10,
                )
                self._client = Redis(connection_pool=self._pool)
                self._client.ping()
                logger.info(f"Redis连接成功: {self._url}")
                return
            except redis.exceptions.ConnectionError as e:
                logger.warning(f"Redis连接失败 ({attempt}/{self._max_retries}): {e}")
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise

    @property
    def client(self) -> Redis:
        """获取Redis客户端"""
        if self._client is None:
            self.connect()
        return self._client

    def close(self) -> None:
        """关闭Redis连接"""
        if self._client:
            self._client.close()
            self._client = None
        if self._pool:
            self._pool.disconnect()
            self._pool = None

    def store_node(self, node: Node, source_id: str) -> None:
        """存储节点到Redis，带重试机制

        存储格式:
        - node:{node_id} -> Hash (所有节点字段)
        - subscription:{source_id}:nodes -> Set (node_id集合)
        """
        node_data = node.to_dict()
        # 将bool和None转为字符串存储
        hash_data = {}
        for k, v in node_data.items():
            if v is None:
                hash_data[k] = ""
            elif isinstance(v, bool):
                hash_data[k] = str(v).lower()
            else:
                hash_data[k] = str(v)

        for attempt in range(1, self._max_retries + 1):
            try:
                pipe = self.client.pipeline()
                pipe.hset(f"node:{node.node_id}", mapping=hash_data)
                pipe.expire(f"node:{node.node_id}", TTL_SECONDS)
                pipe.sadd(f"subscription:{source_id}:nodes", node.node_id)
                pipe.expire(f"subscription:{source_id}:nodes", TTL_SECONDS)
                pipe.execute()
                logger.debug(f"节点存储成功: {node.node_id} (来源: {source_id})")
                return
            except redis.exceptions.RedisError as e:
                logger.warning(f"节点存储失败 ({attempt}/{self._max_retries}): {e}")
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def get_node(self, node_id: str) -> Optional[Node]:
        """从Redis获取节点"""
        data = self.client.hgetall(f"node:{node_id}")
        if not data:
            return None
        return Node.from_dict(data)

    def store_subscription(self, subscription: Subscription) -> None:
        """存储订阅元数据到Redis，带重试机制"""
        meta_data = subscription.to_dict()
        hash_data = {}
        for k, v in meta_data.items():
            if isinstance(v, list):
                hash_data[k] = json.dumps(v, ensure_ascii=False)
            elif v is None:
                hash_data[k] = ""
            else:
                hash_data[k] = str(v)

        for attempt in range(1, self._max_retries + 1):
            try:
                pipe = self.client.pipeline()
                pipe.hset(f"subscription:{subscription.source_id}:meta", mapping=hash_data)
                pipe.expire(f"subscription:{subscription.source_id}:meta", TTL_SECONDS)
                pipe.execute()
                logger.info(f"订阅元数据存储成功: {subscription.source_id}")
                return
            except redis.exceptions.RedisError as e:
                logger.warning(f"订阅存储失败 ({attempt}/{self._max_retries}): {e}")
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def get_subscription(self, source_id: str) -> Optional[Subscription]:
        """从Redis获取订阅元数据"""
        data = self.client.hgetall(f"subscription:{source_id}:meta")
        if not data:
            return None
        return Subscription.from_dict(data)

    def get_node_ids(self, source_id: str) -> list[str]:
        """获取订阅的所有节点ID"""
        return list(self.client.smembers(f"subscription:{source_id}:nodes"))

    def get_nodes_by_source(self, source_id: str) -> list[Node]:
        """获取订阅的所有节点"""
        node_ids = self.get_node_ids(source_id)
        nodes = []
        for node_id in node_ids:
            node = self.get_node(node_id)
            if node:
                nodes.append(node)
        return nodes

    def list_subscriptions(self) -> list[dict]:
        """列出Redis中所有订阅"""
        keys = self.client.keys("subscription:*:meta")
        results = []
        for key in keys:
            source_id = key.split(":")[1]
            meta = self.client.hgetall(key)
            ttl = self.client.ttl(key)
            results.append({
                "source_id": source_id,
                "nodes": meta.get("successful_nodes", "0"),
                "parsed_at": meta.get("parsed_at", ""),
                "ttl": ttl,
            })
        return results

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
