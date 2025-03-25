import logging
import os
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
        """自动扫描weight目录加载所有模型"""
        try:
            weight_dir = Path("weight")
            if not weight_dir.exists():
                logger.error("weight目录不存在")
                return

            # 遍历weight目录下的所有子目录
            for model_dir in weight_dir.iterdir():
                if not model_dir.is_dir():
                    continue

                model_name = model_dir.name
                # 检查是否是检测模型
                detect_model = model_dir / "detect-best.pt"
                if detect_model.exists():
                    try:
                        self._detect_models[model_name] = DetectYOLOModel(
                            str(detect_model)
                        )
                        logger.info(f"成功加载检测模型: {model_name}")
                    except Exception as e:
                        logger.error(f"加载检测模型 {model_name} 失败: {str(e)}")

                # 检查是否是分类模型
                classify_model = model_dir / "classify-best.pt"
                if classify_model.exists():
                    try:
                        self._classify_models[model_name] = ClassifyYOLOModel(
                            str(classify_model)
                        )
                        logger.info(f"成功加载分类模型: {model_name}")
                    except Exception as e:
                        logger.error(f"加载分类模型 {model_name} 失败: {str(e)}")

            if not self._detect_models and not self._classify_models:
                logger.warning("未找到任何模型文件")
            else:
                logger.info(
                    f"模型加载完成，检测模型: {list(self._detect_models.keys())}, "
                    f"分类模型: {list(self._classify_models.keys())}"
                )

        except Exception as e:
            logger.error(f"模型加载过程发生错误: {str(e)}")
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

    def reload_models(self):
        """重新加载所有模型"""
        self._detect_models.clear()
        self._classify_models.clear()
        self._load_models()
