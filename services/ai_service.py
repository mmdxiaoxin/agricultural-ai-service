from typing import Dict, Any, Optional, List
import threading

from common.models.model_manager import ModelManager
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)


class AIService:
    """AI服务类，统一处理模型推理请求（单例模式）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AIService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if not hasattr(self, "_initialized"):
            self.model_manager = ModelManager()
            self._initialized = True

    def detect(
        self, model_name: str, version: str, image_data: bytes
    ) -> Optional[List[Dict[str, Any]]]:
        """
        使用指定版本的YOLO检测模型进行推理

        Args:
            model_name: 模型名称
            version: 模型版本
            image_data: 图片数据

        Returns:
            推理结果列表
        """
        try:
            model = self.model_manager.get_yolo_model(model_name, version, "detect")
            if not model:
                logger.error(f"未找到YOLO检测模型: {model_name}-{version}")
                return None
            results = model.detect(image_data)
            if not isinstance(results, list):
                logger.error("检测结果格式错误")
                return None
            return results

        except Exception as e:
            logger.error(f"检测推理失败: {str(e)}")
            return None

    def classify(
        self, model_name: str, version: str, image_data: bytes
    ) -> Optional[List[Dict[str, Any]]]:
        """
        使用指定版本的模型进行分类推理

        Args:
            model_name: 模型名称
            version: 模型版本
            image_data: 图片数据

        Returns:
            推理结果列表
        """
        try:
            # 直接获取模型
            model = self.model_manager.get_model(model_name, version, "classify")
            if not model:
                logger.error(f"未找到分类模型: {model_name}-{version}")
                return None

            results = model.classify(image_data)
            if not results or not isinstance(results, list):
                logger.error("分类结果格式错误")
                return None
            return results

        except Exception as e:
            logger.error(f"分类推理失败: {str(e)}")
            return None

    def get_available_versions(self) -> Dict[str, list]:
        """获取所有可用的模型版本"""
        return self.model_manager.get_available_versions()
