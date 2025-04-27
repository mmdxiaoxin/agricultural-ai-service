from typing import Dict, Any
import torch
import torchvision.models as models
from common.utils.logger import log_manager

logger = log_manager.get_logger(__name__)

# 确定设备
device = "cuda:0" if torch.cuda.is_available() else "cpu"


class ResNetConfig:
    """ResNet配置类，管理不同版本的ResNet配置"""

    # 支持的ResNet版本
    SUPPORTED_VERSIONS = {
        "resnet18": models.resnet18,
        "resnet34": models.resnet34,
        "resnet50": models.resnet50,
        "resnet101": models.resnet101,
        "resnet152": models.resnet152,
    }

    # 默认配置
    DEFAULT_CONFIG = {
        "device": device,
        "half": True,
        "img_size": 256,
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
    }

    @classmethod
    def get_model_class(cls, version: str):
        """获取指定版本的ResNet模型类"""
        if version not in cls.SUPPORTED_VERSIONS:
            raise ValueError(
                f"不支持的ResNet版本: {version}，支持的版本有: {list(cls.SUPPORTED_VERSIONS.keys())}"
            )
        return cls.SUPPORTED_VERSIONS[version]

    @classmethod
    def get_default_config(cls, version: str) -> Dict[str, Any]:
        """获取指定版本的默认配置"""
        config = cls.DEFAULT_CONFIG.copy()
        config["version"] = version
        return config

    @classmethod
    def get_model_params(cls, version: str) -> Dict[str, Any]:
        """获取指定版本的模型参数"""
        model_class = cls.get_model_class(version)
        return {
            "num_blocks": {
                "resnet18": [2, 2, 2, 2],
                "resnet34": [3, 4, 6, 3],
                "resnet50": [3, 4, 6, 3],
                "resnet101": [3, 4, 23, 3],
                "resnet152": [3, 8, 36, 3],
            }[version],
            "block_type": (
                "basic" if version in ["resnet18", "resnet34"] else "bottleneck"
            ),
        }

    @classmethod
    def get_model_info(cls, version: str) -> Dict[str, Any]:
        """获取指定版本的模型信息"""
        return {
            "version": version,
            "params": cls.get_model_params(version),
            "config": cls.get_default_config(version),
        }
