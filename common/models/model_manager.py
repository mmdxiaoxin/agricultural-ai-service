from pathlib import Path
from typing import Dict, Optional, Any
import hashlib
import threading

from common.models.resnet_model import ResNetModel
from common.models.yolo_model import DetectYOLOModel, ClassifyYOLOModel
from common.database import ModelDB, VersionDB, TaskDB, DatabaseUtils
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

            # 初始化数据库操作类
            self._model_db = ModelDB()
            self._version_db = VersionDB()
            self._task_db = TaskDB()
            self._db_utils = DatabaseUtils()

            self._model_locks: Dict[str, threading.Lock] = {}  # 每个模型的操作锁
            self._initialized = True

            # 配置ONNX Runtime
            self._configure_onnx_runtime()

            # 验证数据库数据完整性
            if not self._db_utils.verify_model_data():
                logger.error("数据库验证失败，模型数据可能不完整")

            self._load_models()

    def _configure_onnx_runtime(self):
        """配置ONNX Runtime"""
        try:
            import onnxruntime as ort

            # 设置日志级别为WARNING
            ort.set_default_logger_severity(2)  # 2 = WARNING

            # 创建会话选项
            self._session_options = ort.SessionOptions()

            # 配置CUDA执行提供程序选项
            cuda_provider_options = {
                "device_id": 0,
                "arena_extend_strategy": "kNextPowerOfTwo",
                "gpu_mem_limit": 2 * 1024 * 1024 * 1024,  # 2GB
                "cudnn_conv_algo_search": "EXHAUSTIVE",
                "do_copy_in_default_stream": False,  # 禁用默认流中的拷贝
                "enable_cuda_graph": True,  # 启用CUDA图优化
                "cuda_graph_compile_mode": "LAZY",  # 使用延迟编译模式
                "enable_mem_pattern": True,  # 启用内存模式优化
                "enable_mem_reuse": True,  # 启用内存重用
            }

            # 设置会话选项
            self._session_options.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            )
            self._session_options.intra_op_num_threads = 1
            self._session_options.inter_op_num_threads = 1
            self._session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            self._session_options.enable_mem_pattern = True  # 启用内存模式优化
            self._session_options.enable_mem_reuse = True  # 启用内存重用
            self._session_options.enable_cpu_mem_arena = True  # 启用CPU内存池

            logger.info("ONNX Runtime配置完成")

        except Exception as e:
            logger.warning(f"ONNX Runtime配置失败: {str(e)}")
            self._session_options = None

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
                models = self._model_db.get_all_models()
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
                            model_data = self._model_db.get_model(model_name, version)

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
                                                session_options=getattr(
                                                    self, "_session_options", None
                                                ),
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
                                                session_options=getattr(
                                                    self, "_session_options", None
                                                ),
                                            )
                                            logger.info(
                                                f"成功加载YOLO分类模型: {model_name}-{version}"
                                            )

                                elif model_type.startswith("resnet"):
                                    if model_name not in self._resnet_models:
                                        self._resnet_models[model_name] = {}
                                    # 从模型名称中提取ResNet版本
                                    resnet_version = model_type
                                    self._resnet_models[model_name][version] = (
                                        ResNetModel(
                                            model_data["file_path"],
                                            version=resnet_version,
                                            params=model_data["parameters"],
                                            session_options=getattr(
                                                self, "_session_options", None
                                            ),
                                        )
                                    )
                                    logger.info(
                                        f"成功加载ResNet模型: {model_name}-{version} ({resnet_version})"
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
        file_size: int,
        file_hash: str,
        model_version: str,
        model_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> bool:
        """添加新模型"""
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"模型文件不存在: {file_path}")

            # 添加到数据库
            if self._model_db.add_model(
                name=name,
                version=version,
                task_type=task_type,
                file_path=str(file_path),
                file_size=file_size,
                file_hash=file_hash,
                model_version=model_version,
                model_type=model_type,
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
            model_data = self._model_db.get_model(model_name, version)
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
                        model_data["file_path"],
                        model_data["parameters"],
                        session_options=getattr(self, "_session_options", None),
                    )
                elif task_type == "classify":
                    self._yolo_models[model_name][version][task_type] = (
                        ClassifyYOLOModel(
                            model_data["file_path"],
                            model_data["parameters"],
                            session_options=getattr(self, "_session_options", None),
                        )
                    )

            return self._yolo_models[model_name][version].get(task_type)

    def get_resnet_model(self, model_name: str, version: str) -> Optional[ResNetModel]:
        """获取指定ResNet模型（线程安全）"""
        model_key = f"{model_name}_{version}"
        with self._get_model_lock(model_key):
            # 从数据库获取模型信息
            model_data = self._model_db.get_model(model_name, version)
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
                # 从模型名称中提取ResNet版本
                resnet_version = model_name.split("_")[0].lower()
                # 加载模型
                self._resnet_models[model_name][version] = ResNetModel(
                    model_data["file_path"],
                    version=resnet_version,
                    params=model_data["parameters"],
                )

            return self._resnet_models[model_name][version]

    def get_available_versions(self) -> Dict[str, list]:
        """获取所有可用的模型版本"""
        return self._model_db.get_all_models()

    def get_model_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取模型信息"""
        return self._model_db.get_model_by_id(model_id)

    def get_model_by_version_id(self, version_id: int) -> Optional[Dict[str, Any]]:
        """根据版本ID获取模型信息"""
        return self._version_db.get_version_by_id(version_id)

    def update_model_parameters(
        self, model_id: int, parameters: Dict[str, Any]
    ) -> bool:
        """更新模型参数"""
        return self._version_db.update_version_parameters(model_id, parameters)

    def delete_model_by_id(self, model_id: int) -> bool:
        """根据ID删除模型"""
        return self._model_db.delete_model_by_id(model_id)

    def delete_version_by_id(self, version_id: int) -> bool:
        """根据版本ID删除模型版本"""
        try:
            # 获取版本信息
            version_info = self._version_db.get_version_by_id(version_id)
            if not version_info:
                logger.warning(f"未找到版本信息: ID={version_id}")
                return False

            # 删除模型文件
            file_path = Path(version_info["file_path"])
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"模型文件已删除: {file_path}")
                except Exception as e:
                    logger.error(f"删除模型文件失败: {str(e)}")
                    return False

            # 删除数据库记录
            if not self._version_db.delete_version_by_id(version_id):
                return False

            # 重新加载模型
            self._load_models()
            return True
        except Exception as e:
            logger.error(f"删除模型版本失败: {str(e)}")
            return False

    def get_model_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """根据文件哈希获取模型信息"""
        return self._model_db.get_model_by_hash(file_hash)

    def get_model(
        self, model_name: str, version: str, task_type: Optional[str] = None
    ) -> Optional[Any]:
        """
        根据模型名称直接获取模型（线程安全）

        Args:
            model_name: 模型名称
            version: 模型版本
            task_type: 任务类型（可选，仅用于YOLO模型）

        Returns:
            对应的模型实例
        """
        model_key = f"{model_name}_{version}"
        with self._get_model_lock(model_key):
            # 从数据库获取模型信息
            model_data = self._model_db.get_model(model_name, version)
            if not model_data:
                logger.warning(f"未找到模型: {model_name}-{version}")
                return None

            # 根据模型名称判断模型类型
            if model_name.startswith("resnet"):
                # 检查任务类型是否支持
                if "classify" not in model_data["task_types"]:
                    logger.warning(f"模型 {model_name}-{version} 不支持分类任务")
                    return None

                # 获取或加载ResNet模型
                if model_name not in self._resnet_models:
                    self._resnet_models[model_name] = {}
                if version not in self._resnet_models[model_name]:
                    # 从模型名称中提取ResNet版本
                    resnet_version = model_name.split("_")[0].lower()
                    # 加载模型
                    self._resnet_models[model_name][version] = ResNetModel(
                        model_data["file_path"],
                        version=resnet_version,
                        params=model_data["parameters"],
                        session_options=getattr(self, "_session_options", None),
                    )
                return self._resnet_models[model_name][version]
            else:
                # 检查任务类型是否支持
                if task_type and task_type not in model_data["task_types"]:
                    logger.warning(
                        f"模型 {model_name}-{version} 不支持任务类型: {task_type}"
                    )
                    return None

                # 获取或加载YOLO模型
                if model_name not in self._yolo_models:
                    self._yolo_models[model_name] = {}
                if version not in self._yolo_models[model_name]:
                    self._yolo_models[model_name][version] = {}
                if (
                    task_type
                    and task_type not in self._yolo_models[model_name][version]
                ):
                    # 加载模型
                    if task_type == "detect":
                        self._yolo_models[model_name][version][task_type] = (
                            DetectYOLOModel(
                                model_data["file_path"],
                                model_data["parameters"],
                                session_options=getattr(self, "_session_options", None),
                            )
                        )
                    elif task_type == "classify":
                        self._yolo_models[model_name][version][task_type] = (
                            ClassifyYOLOModel(
                                model_data["file_path"],
                                model_data["parameters"],
                                session_options=getattr(self, "_session_options", None),
                            )
                        )
                return (
                    self._yolo_models[model_name][version].get(task_type)
                    if task_type
                    else None
                )

    def initialize(self, model_db):
        """初始化模型管理器"""
        if self._initialized:
            return

        self._model_db = model_db
        self._initialized = True

        # 预加载常用模型
        self._preload_models()

    def _preload_models(self):
        """预加载常用模型"""
        try:
            # 获取所有模型元数据
            all_models = self._model_db.get_all_models()

            # 预加载每个模型
            for model_data in all_models:
                if not isinstance(model_data, dict):
                    continue

                model_name = str(model_data.get("name", ""))
                version = str(model_data.get("version", ""))
                task_types = model_data.get("task_types", [])

                if not model_name or not version or not task_types:
                    continue

                # 预加载YOLO模型
                if model_name.startswith("yolo"):
                    for task_type in task_types:
                        self.get_yolo_model(model_name, version, task_type)
                # 预加载ResNet模型
                elif model_name.startswith("resnet"):
                    self.get_resnet_model(model_name, version)

            logger.info("模型预加载完成")
        except Exception as e:
            logger.error(f"模型预加载失败: {str(e)}")
