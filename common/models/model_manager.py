import logging
from typing import Dict, Optional, Union
from pathlib import Path

from common.models.base_model import DetectYOLOModel, ClassifyYOLOModel

logger = logging.getLogger(__name__)


class ModelManager:
    """模型管理器，用于统一管理不同版本的模型"""

    _instance = None
    _detect_models: Dict[str, DetectYOLOModel] = {}
    _classify_models: Dict[str, ClassifyYOLOModel] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._load_models()

    def _load_models(self):
        """加载所有模型"""
        try:
            # 检测模型
            self._detect_models = {
                "yolo5": DetectYOLOModel("models/yolo5.pt"),
                "yolo8": DetectYOLOModel("models/yolo8.pt"),
            }

            # 分类模型
            self._classify_models = {
                "yolo11": ClassifyYOLOModel("models/yolo11.pt"),
            }

            logger.info("所有模型加载完成")
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            raise

    def get_detect_model(self, version: str) -> Optional[DetectYOLOModel]:
        """获取指定版本的检测模型"""
        if version not in self._detect_models:
            logger.error(f"未找到检测模型版本: {version}")
            return None
        return self._detect_models[version]

    def get_classify_model(self, version: str) -> Optional[ClassifyYOLOModel]:
        """获取指定版本的分类模型"""
        if version not in self._classify_models:
            logger.error(f"未找到分类模型版本: {version}")
            return None
        return self._classify_models[version]

    def get_available_versions(self) -> Dict[str, list]:
        """获取所有可用的模型版本"""
        return {
            "detect": list(self._detect_models.keys()),
            "classify": list(self._classify_models.keys()),
        }
