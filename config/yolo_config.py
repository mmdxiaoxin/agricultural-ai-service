from typing import Dict, Any
import torch
from common.utils.logger import log_manager

logger = log_manager.get_logger(__name__)

# 确定设备
device = "cuda:0" if torch.cuda.is_available() else "cpu"


class YOLOConfig:
    """YOLO配置类，管理YOLO模型的配置"""

    # 默认配置
    DEFAULT_CONFIG = {
        "device": device,
        "conf": 0.25,  # 置信度阈值
        "iou": 0.5,  # IoU阈值
        "classes": None,  # 指定类别
        "verbose": False,  # 是否显示详细信息
        "half": True,  # 是否使用半精度推理
        "agnostic_nms": False,  # 是否使用类别无关的NMS
        "max_det": 300,  # 最大检测框数量
    }

    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """获取默认配置"""
        return cls.DEFAULT_CONFIG.copy()

    @classmethod
    def get_model_info(cls) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "config": cls.get_default_config(),
            "device": device,
        }
