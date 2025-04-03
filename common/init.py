from typing import Optional

from common.models.model_manager import ModelManager
from common.database import ModelDB, VersionDB, TaskDB, DatabaseUtils
from common.utils.redis_utils import RedisClient
from services.ai_service import AIService
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)


class ServiceInitializer:
    """服务初始化器，统一管理所有组件的初始化"""

    _instance: Optional["ServiceInitializer"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceInitializer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._model_manager: Optional[ModelManager] = None
            self._ai_service: Optional[AIService] = None
            self._redis_client: Optional[RedisClient] = None
            self._model_db: Optional[ModelDB] = None
            self._version_db: Optional[VersionDB] = None
            self._task_db: Optional[TaskDB] = None
            self._db_utils: Optional[DatabaseUtils] = None

    def init_all(self):
        """初始化所有服务组件"""
        try:
            # 初始化Redis客户端
            self._init_redis()

            # 初始化数据库
            self._init_database()

            # 初始化模型管理器
            self._init_model_manager()

            # 初始化AI服务
            self._init_ai_service()

            logger.info("所有服务组件初始化完成")
            return True
        except Exception as e:
            logger.error(f"服务初始化失败: {str(e)}")
            raise

    def _init_redis(self):
        """初始化Redis客户端"""
        try:
            self._redis_client = RedisClient()
            logger.info("Redis客户端初始化成功")
        except Exception as e:
            logger.error(f"Redis客户端初始化失败: {str(e)}")
            raise

    def _init_database(self):
        """初始化数据库"""
        try:
            self._model_db = ModelDB()
            self._version_db = VersionDB()
            self._task_db = TaskDB()
            self._db_utils = DatabaseUtils()
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise

    def _init_model_manager(self):
        """初始化模型管理器"""
        try:
            self._model_manager = ModelManager()
            logger.info("模型管理器初始化成功")
        except Exception as e:
            logger.error(f"模型管理器初始化失败: {str(e)}")
            raise

    def _init_ai_service(self):
        """初始化AI服务"""
        try:
            self._ai_service = AIService()
            logger.info("AI服务初始化成功")
        except Exception as e:
            logger.error(f"AI服务初始化失败: {str(e)}")
            raise

    @property
    def model_manager(self) -> ModelManager:
        """获取模型管理器实例"""
        if self._model_manager is None:
            self._init_model_manager()
        assert self._model_manager is not None
        return self._model_manager

    @property
    def ai_service(self) -> AIService:
        """获取AI服务实例"""
        if self._ai_service is None:
            self._init_ai_service()
        assert self._ai_service is not None
        return self._ai_service

    @property
    def redis_client(self) -> RedisClient:
        """获取Redis客户端实例"""
        if self._redis_client is None:
            self._init_redis()
        assert self._redis_client is not None
        return self._redis_client

    @property
    def model_db(self) -> ModelDB:
        """获取模型数据库实例"""
        if self._model_db is None:
            self._init_database()
        assert self._model_db is not None
        return self._model_db

    @property
    def version_db(self) -> VersionDB:
        """获取版本数据库实例"""
        if self._version_db is None:
            self._init_database()
        assert self._version_db is not None
        return self._version_db

    @property
    def task_db(self) -> TaskDB:
        """获取任务数据库实例"""
        if self._task_db is None:
            self._init_database()
        assert self._task_db is not None
        return self._task_db

    @property
    def db_utils(self) -> DatabaseUtils:
        """获取数据库工具实例"""
        if self._db_utils is None:
            self._init_database()
        assert self._db_utils is not None
        return self._db_utils


# 创建全局初始化器实例
initializer = ServiceInitializer()
