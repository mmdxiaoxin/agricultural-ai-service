import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import logging
from typing import Dict, Any
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
    "yolo5": {
        "type": "detect",
        "path": Config.WEIGHT_DIR / "yolo5" / "detect-best.pt",
        "conf": 0.25,
        "iou": 0.5,
    },
    "yolo8": {
        "type": "detect",
        "path": Config.WEIGHT_DIR / "yolo8" / "detect-best.pt",
        "conf": 0.25,
        "iou": 0.5,
    },
    "yolo11": {
        "type": "classify",
        "path": Config.WEIGHT_DIR / "yolo11" / "classify-best.pt",
        "conf": 0.25,
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
        for version, config in DEFAULT_MODEL_CONFIGS.items():
            model_path = config["path"]
            model_type = config["type"]

            # 检查模型文件是否存在
            if not model_path.exists():
                logger.warning(f"模型文件不存在: {model_path}")
                continue

            # 计算文件哈希和大小
            file_hash = calculate_file_hash(model_path)
            file_size = model_path.stat().st_size

            # 准备模型参数
            parameters = {
                "conf": config.get("conf", 0.25),
                "iou": config.get("iou", 0.5),
            }

            # 添加到数据库
            if db.add_model(
                version=version,
                model_type=model_type,
                file_path=str(model_path),
                file_size=file_size,
                file_hash=file_hash,
                parameters=parameters,
            ):
                logger.info(f"成功迁移模型: {version}-{model_type}")
            else:
                logger.error(f"迁移模型失败: {version}-{model_type}")

        # 验证迁移结果
        models = db.get_all_models()
        logger.info("迁移完成，当前模型列表:")
        logger.info(f"检测模型: {models['detect']}")
        logger.info(f"分类模型: {models['classify']}")

    except Exception as e:
        logger.error(f"迁移过程发生错误: {str(e)}")
        raise


if __name__ == "__main__":
    migrate_models()
