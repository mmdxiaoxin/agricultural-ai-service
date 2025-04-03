from pathlib import Path
from typing import Dict, Optional, Any
import hashlib
import threading

from common.models.base_model import DetectYOLOModel, ClassifyYOLOModel, ResNetModel
from common.models.database import Database
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)


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
            # 按模型类型组织
            self._yolo_models: Dict[str, Dict[str, Dict[str, Any]]] = (
                {}
            )  # model_name -> version -> task_type -> model
            self._resnet_models: Dict[str, Dict[str, ResNetModel]] = (
                {}
            )  # model_name -> version -> model
            self._db = Database()
            self._model_locks: Dict[str, threading.Lock] = {}  # 每个模型的操作锁
            self._initialized = True

            # 验证数据库数据完整性
            if not self._db.verify_model_data():
                logger.error("数据库验证失败，模型数据可能不完整")

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
                if not models:
                    logger.warning("数据库中没有找到任何模型")
                    return

                logger.info(f"从数据库获取到的模型列表: {models}")

                # 清空现有模型
                self._yolo_models.clear()
                self._resnet_models.clear()

                # 遍历所有模型
                for model_name, versions in models.items():
                    if not versions:
                        logger.warning(f"模型 {model_name} 没有版本信息")
                        continue

                    model_type = model_name.split("_")[
                        0
                    ].lower()  # 从模型名称提取类型（yolo/resnet）

                    for version_info in versions:
                        version = version_info.get("version")
                        task_types = version_info.get("task_types", [])

                        if not version:
                            logger.warning(f"模型 {model_name} 的版本信息不完整")
                            continue

                        try:
                            logger.info(f"开始加载模型: {model_name}-{version}")
                            model_data = self._db.get_model(model_name, version)

                            if not model_data:
                                logger.warning(
                                    f"未找到模型数据: {model_name}-{version}"
                                )
                                continue

                            logger.info(f"获取到的模型数据: {model_data}")

                            if model_data and Path(model_data["file_path"]).exists():
                                logger.info(f"模型文件存在: {model_data['file_path']}")
                                # 设置模型的输出控制
                                model_data["parameters"] = model_data.get(
                                    "parameters", {}
                                )
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

                                # 根据模型类型加载
                                if model_type == "yolo":
                                    if model_name not in self._yolo_models:
                                        self._yolo_models[model_name] = {}
                                    if version not in self._yolo_models[model_name]:
                                        self._yolo_models[model_name][version] = {}

                                    # 加载YOLO模型的不同任务
                                    for task_type in task_types:
                                        if task_type == "detect":
                                            self._yolo_models[model_name][version][
                                                "detect"
                                            ] = DetectYOLOModel(
                                                model_data["file_path"],
                                                model_data["parameters"],
                                            )
                                            logger.info(
                                                f"成功加载YOLO检测模型: {model_name}-{version}"
                                            )
                                        elif task_type == "classify":
                                            self._yolo_models[model_name][version][
                                                "classify"
                                            ] = ClassifyYOLOModel(
                                                model_data["file_path"],
                                                model_data["parameters"],
                                            )
                                            logger.info(
                                                f"成功加载YOLO分类模型: {model_name}-{version}"
                                            )

                                elif model_type == "resnet18":
                                    if model_name not in self._resnet_models:
                                        self._resnet_models[model_name] = {}
                                    self._resnet_models[model_name][version] = (
                                        ResNetModel(
                                            model_data["file_path"],
                                            model_data["parameters"],
                                        )
                                    )
                                    logger.info(
                                        f"成功加载ResNet模型: {model_name}-{version}"
                                    )
                            else:
                                logger.warning(
                                    f"模型文件不存在: {model_name}-{version}, 路径: {model_data['file_path'] if model_data else 'None'}"
                                )
                        except Exception as e:
                            logger.error(
                                f"加载模型 {model_name}-{version} 失败: {str(e)}",
                                exc_info=True,
                            )

                if not self._yolo_models and not self._resnet_models:
                    logger.warning("未找到任何模型文件")
                else:
                    logger.info(
                        f"模型加载完成，YOLO模型: {list(self._yolo_models.keys())}, ResNet模型: {list(self._resnet_models.keys())}"
                    )

            except Exception as e:
                logger.error(f"模型加载过程发生错误: {str(e)}", exc_info=True)
                raise

    def add_model(
        self,
        name: str,
        version: str,
        task_type: str,
        file_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
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
                name=name,
                version=version,
                task_type=task_type,
                file_path=str(file_path),
                file_size=file_size,
                file_hash=file_hash,
                parameters=parameters,
                description=description,
            ):
                # 重新加载模型
                self._load_models()
                return True
            return False

        except Exception as e:
            logger.error(f"添加模型失败: {str(e)}")
            return False

    def get_yolo_model(
        self, model_name: str, version: str, task_type: str
    ) -> Optional[Any]:
        """获取指定YOLO模型（线程安全）"""
        model_key = f"{model_name}_{version}_{task_type}"
        with self._get_model_lock(model_key):
            # 从数据库获取模型信息
            model_data = self._db.get_model(model_name, version)
            if not model_data:
                logger.warning(f"未找到模型: {model_name}-{version}")
                return None

            # 检查任务类型是否支持
            if task_type not in model_data["task_types"]:
                logger.warning(
                    f"模型 {model_name}-{version} 不支持任务类型: {task_type}"
                )
                return None

            # 获取或加载模型
            if model_name not in self._yolo_models:
                self._yolo_models[model_name] = {}
            if version not in self._yolo_models[model_name]:
                self._yolo_models[model_name][version] = {}
            if task_type not in self._yolo_models[model_name][version]:
                # 加载模型
                if task_type == "detect":
                    self._yolo_models[model_name][version][task_type] = DetectYOLOModel(
                        model_data["file_path"], model_data["parameters"]
                    )
                elif task_type == "classify":
                    self._yolo_models[model_name][version][task_type] = (
                        ClassifyYOLOModel(
                            model_data["file_path"], model_data["parameters"]
                        )
                    )

            return self._yolo_models[model_name][version].get(task_type)

    def get_resnet_model(self, model_name: str, version: str) -> Optional[ResNetModel]:
        """获取指定ResNet模型（线程安全）"""
        model_key = f"{model_name}_{version}"
        with self._get_model_lock(model_key):
            # 从数据库获取模型信息
            model_data = self._db.get_model(model_name, version)
            if not model_data:
                logger.warning(f"未找到模型: {model_name}-{version}")
                return None

            # 检查任务类型是否支持
            if "classify" not in model_data["task_types"]:
                logger.warning(f"模型 {model_name}-{version} 不支持分类任务")
                return None

            # 获取或加载模型
            if model_name not in self._resnet_models:
                self._resnet_models[model_name] = {}
            if version not in self._resnet_models[model_name]:
                # 加载模型
                self._resnet_models[model_name][version] = ResNetModel(
                    model_data["file_path"], model_data["parameters"]
                )

            return self._resnet_models[model_name][version]

    def get_available_versions(self) -> Dict[str, list]:
        """获取所有可用的模型版本"""
        return self._db.get_all_models()

    def delete_model(self, name: str, version: str) -> bool:
        """删除指定版本的模型"""
        try:
            # 从数据库中删除元数据
            if self._db.delete_model(name, version):
                # 重新加载模型
                self._load_models()
                return True
            return False
        except Exception as e:
            logger.error(f"删除模型失败: {str(e)}")
            return False

    def get_model_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取模型信息"""
        return self._db.get_model_by_id(model_id)

    def update_model_parameters(
        self, model_id: int, parameters: Dict[str, Any]
    ) -> bool:
        """更新模型参数"""
        return self._db.update_model_parameters(model_id, parameters)

    def delete_model_by_id(self, model_id: int) -> bool:
        """根据ID删除模型"""
        return self._db.delete_model_by_id(model_id)
