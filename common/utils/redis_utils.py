import json
from typing import Any, Optional
import redis
from config.app_config import Config
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)


class RedisClient:
    """Redis客户端单例类"""

    _instance = None
    _client = None

    @classmethod
    def get_instance(cls) -> redis.Redis:
        """获取Redis客户端实例"""
        if cls._client is None:
            try:
                cls._client = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    password=Config.REDIS_PASSWORD,
                    decode_responses=True,  # 自动解码响应
                    socket_timeout=5,  # 连接超时时间
                    socket_connect_timeout=5,  # 连接超时时间
                    retry_on_timeout=True,  # 超时重试
                )
                # 测试连接
                cls._client.ping()
                logger.info("Redis连接成功")
            except Exception as e:
                logger.error(f"Redis连接失败: {str(e)}")
                raise
        return cls._client

    @classmethod
    def set_cache(cls, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            client = cls.get_instance()
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            client.set(key, value, ex=ttl or Config.REDIS_CACHE_TTL)
            return True
        except Exception as e:
            logger.error(f"设置Redis缓存失败: {str(e)}")
            return False

    @classmethod
    def get_cache(cls, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            client = cls.get_instance()
            value = client.get(key)
            if value:
                try:
                    # 确保value是字符串类型
                    if isinstance(value, bytes):
                        value = value.decode("utf-8")
                    elif not isinstance(value, str):
                        value = str(value)
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"获取Redis缓存失败: {str(e)}")
            return None

    @classmethod
    def delete_cache(cls, key: str) -> bool:
        """删除缓存"""
        try:
            client = cls.get_instance()
            client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除Redis缓存失败: {str(e)}")
            return False

    @classmethod
    def clear_cache(cls) -> bool:
        """清空所有缓存"""
        try:
            client = cls.get_instance()
            client.flushdb()
            return True
        except Exception as e:
            logger.error(f"清空Redis缓存失败: {str(e)}")
            return False
