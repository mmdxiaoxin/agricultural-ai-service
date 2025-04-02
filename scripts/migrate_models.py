import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import logging
from typing import Dict, Any, List
import hashlib
from datetime import datetime

from common.models.database import Database
from config.app_config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 默认模型配置
DEFAULT_MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "yolo_v5": {
        "versions": {
            "1.0.0": {
                "tasks": ["detect"],  # 支持的任务类型
                "path": Config.WEIGHT_DIR / "yolo5" / "detect-best.pt",
                "description": "YOLOv5目标检测模型",
                "parameters": {
                    "conf": 0.25,
                    "iou": 0.5,
                },
            }
        }
    },
    "yolo_v8": {
        "versions": {
            "1.0.0": {
                "tasks": ["detect"],
                "path": Config.WEIGHT_DIR / "yolo8" / "detect-best.pt",
                "description": "YOLOv8目标检测模型",
                "parameters": {
                    "conf": 0.25,
                    "iou": 0.5,
                },
            },
        }
    },
    "resnet18": {
        "versions": {
            "1.0.0": {
                "tasks": ["classify"],
                "path": Config.WEIGHT_DIR / "resnet" / "best_model.pth",
                "description": "ResNet18图像分类模型",
                "parameters": {"img_size": 224, "half": True},
            }
        }
    },
}


def calculate_file_hash(file_path: Path) -> str:
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def migrate_models():
    """迁移模型配置到数据库"""
    try:
        # 初始化数据库
        db = Database()
        logger.info("开始迁移模型配置...")

        # 遍历所有模型配置
        for model_name, model_info in DEFAULT_MODEL_CONFIGS.items():
            logger.info(f"开始处理模型: {model_name}")

            # 遍历模型的所有版本
            for version, version_info in model_info["versions"].items():
                model_path = version_info["path"]
                tasks = version_info["tasks"]
                description = version_info.get("description", "")
                parameters = version_info.get("parameters", {})

                # 检查模型文件是否存在
                if not model_path.exists():
                    logger.warning(f"模型文件不存在: {model_path}")
                    continue

                # 计算文件哈希和大小
                file_hash = calculate_file_hash(model_path)
                file_size = model_path.stat().st_size

                # 为每个任务类型添加模型
                for task in tasks:
                    if db.add_model(
                        name=model_name,
                        version=version,
                        task_type=task,
                        file_path=str(model_path),
                        file_size=file_size,
                        file_hash=file_hash,
                        parameters=parameters,
                        description=description,
                    ):
                        logger.info(f"成功迁移模型: {model_name}-{version}-{task}")
                    else:
                        logger.error(f"迁移模型失败: {model_name}-{version}-{task}")

        # 验证迁移结果
        models = db.get_all_models()
        logger.info("迁移完成，当前模型列表:")
        for model_name, versions in models.items():
            logger.info(f"\n模型: {model_name}")
            for version_info in versions:
                logger.info(f"  版本: {version_info['version']}")
                logger.info(f"  模型类型: {version_info['model_type']}")
                logger.info(f"  任务类型: {version_info['task_types']}")
                logger.info(f"  描述: {version_info['description']}")

    except Exception as e:
        logger.error(f"迁移过程发生错误: {str(e)}")
        raise


if __name__ == "__main__":
    migrate_models()
