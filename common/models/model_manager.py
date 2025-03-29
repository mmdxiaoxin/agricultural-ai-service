import logging
from pathlib import Path
from typing import Dict, Optional, Any
import hashlib
from datetime import datetime
import threading

from common.models.base_model import DetectYOLOModel, ClassifyYOLOModel
from common.models.database import Database
from common.utils.exceptions import ModelError

logger = logging.getLogger(__name__)


class ModelManager:
    """模型管理器，负责模型的加载和管理（单例模式）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if not hasattr(self, "_initialized"):
            self._detect_models: Dict[str, DetectYOLOModel] = {}
            self._classify_models: Dict[str, ClassifyYOLOModel] = {}
            self._db = Database()
            self._model_locks: Dict[str, threading.Lock] = {}  # 每个模型的操作锁
            self._initialized = True
            self._load_models()

    def _get_model_lock(self, model_key: str) -> threading.Lock:
        """获取模型的操作锁"""
        if model_key not in self._model_locks:
            with self._lock:
                if model_key not in self._model_locks:
                    self._model_locks[model_key] = threading.Lock()
        return self._model_locks[model_key]

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件的MD5哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _load_models(self):
        """从数据库加载所有模型（线程安全）"""
        with self._lock:
            try:
                # 获取所有模型元数据
                models = self._db.get_all_models()
                logger.info(f"从数据库获取到的模型列表: {models}")

                # 加载检测模型
                for version in models["detect"]:
                    try:
                        logger.info(f"开始加载检测模型: {version}")
                        model_data = self._db.get_model(version, "detect")
                        logger.info(f"获取到的模型数据: {model_data}")

                        if model_data and Path(model_data["file_path"]).exists():
                            logger.info(f"模型文件存在: {model_data['file_path']}")
                            # 设置YOLOv8模型的输出控制
                            model_data["parameters"] = model_data.get("parameters", {})
                            model_data["parameters"].update(
                                {
                                    "verbose": False,  # 禁用详细输出
                                    "show": False,  # 禁用显示
                                    "save": False,  # 禁用保存
                                }
                            )
                            logger.info(
                                f"准备加载模型，参数: {model_data['parameters']}"
                            )
                            self._detect_models[version] = DetectYOLOModel(
                                model_data["file_path"], model_data["parameters"]
                            )
                            logger.info(f"成功加载检测模型: {version}")
                        else:
                            logger.warning(
                                f"检测模型文件不存在: {version}, 路径: {model_data['file_path'] if model_data else 'None'}"
                            )
                    except Exception as e:
                        logger.error(
                            f"加载检测模型 {version} 失败: {str(e)}", exc_info=True
                        )

                # 加载分类模型
                for version in models["classify"]:
                    try:
                        logger.info(f"开始加载分类模型: {version}")
                        model_data = self._db.get_model(version, "classify")
                        logger.info(f"获取到的模型数据: {model_data}")

                        if model_data and Path(model_data["file_path"]).exists():
                            logger.info(f"模型文件存在: {model_data['file_path']}")
                            model_data["parameters"] = model_data.get("parameters", {})
                            model_data["parameters"].update(
                                {
                                    "verbose": False,  # 禁用详细输出
                                    "show": False,  # 禁用显示
                                    "save": False,  # 禁用保存
                                }
                            )
                            logger.info(
                                f"准备加载模型，参数: {model_data['parameters']}"
                            )
                            self._classify_models[version] = ClassifyYOLOModel(
                                model_data["file_path"], model_data["parameters"]
                            )
                            logger.info(f"成功加载分类模型: {version}")
                        else:
                            logger.warning(
                                f"分类模型文件不存在: {version}, 路径: {model_data['file_path'] if model_data else 'None'}"
                            )
                    except Exception as e:
                        logger.error(
                            f"加载分类模型 {version} 失败: {str(e)}", exc_info=True
                        )

                if not self._detect_models and not self._classify_models:
                    logger.warning("未找到任何模型文件")
                else:
                    logger.info(
                        f"模型加载完成，检测模型: {list(self._detect_models.keys())}, "
                        f"分类模型: {list(self._classify_models.keys())}"
                    )

            except Exception as e:
                logger.error(f"模型加载过程发生错误: {str(e)}", exc_info=True)
                raise

    def add_model(
        self,
        version: str,
        model_type: str,
        file_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """添加新模型"""
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"模型文件不存在: {file_path}")

            # 计算文件哈希
            file_hash = self._calculate_file_hash(file_path)
            file_size = file_path.stat().st_size

            # 添加到数据库
            if self._db.add_model(
                version=version,
                model_type=model_type,
                file_path=str(file_path),
                file_size=file_size,
                file_hash=file_hash,
                parameters=parameters,
            ):
                # 重新加载模型
                self._load_models()
                return True
            return False

        except Exception as e:
            logger.error(f"添加模型失败: {str(e)}")
            return False

    def get_detect_model(self, version: str) -> Optional[DetectYOLOModel]:
        """获取指定版本的检测模型（线程安全）"""
        model_key = f"detect_{version}"
        with self._get_model_lock(model_key):
            return self._detect_models.get(version)

    def get_classify_model(self, version: str) -> Optional[ClassifyYOLOModel]:
        """获取指定版本的分类模型（线程安全）"""
        model_key = f"classify_{version}"
        with self._get_model_lock(model_key):
            return self._classify_models.get(version)

    def get_available_versions(self) -> Dict[str, list]:
        """获取所有可用的模型版本"""
        return self._db.get_all_models()

    def delete_model(self, version: str, model_type: str) -> bool:
        """删除指定版本的模型"""
        try:
            # 从数据库中删除元数据
            if self._db.delete_model(version, model_type):
                # 从内存中删除模型
                if model_type == "detect":
                    self._detect_models.pop(version, None)
                elif model_type == "classify":
                    self._classify_models.pop(version, None)
                return True
            return False
        except Exception as e:
            logger.error(f"删除模型失败: {str(e)}")
            return False
