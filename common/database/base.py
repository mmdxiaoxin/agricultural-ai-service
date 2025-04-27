import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime
from common.utils.logger import log_manager
from config.app_config import Config

# 获取日志记录器
logger = log_manager.get_logger(__name__)


class DatabaseBase:
    """数据库基础操作类"""

    def __init__(self, db_path: str = "models.db"):
        # 确保 data 目录存在
        data_dir = Config.BASE_DIR / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # 设置数据库文件路径
        self.db_path = str(data_dir / db_path)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 创建模型基本信息表
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        model_type TEXT NOT NULL,  -- yolo, resnet等
                        model_version TEXT NOT NULL,  -- 具体模型版本（如v8, v5, 18, 50等）
                        description TEXT,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        UNIQUE(name)
                    )
                """
                )

                # 创建模型版本表
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        model_id INTEGER NOT NULL,
                        version TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        file_hash TEXT NOT NULL,
                        parameters TEXT,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (model_id) REFERENCES models(id),
                        UNIQUE(model_id, version)
                    )
                """
                )

                # 创建任务类型表
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        UNIQUE(name)
                    )
                """
                )

                # 创建版本-任务关联表
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS version_tasks (
                        version_id INTEGER NOT NULL,
                        task_id INTEGER NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        PRIMARY KEY (version_id, task_id),
                        FOREIGN KEY (version_id) REFERENCES versions(id),
                        FOREIGN KEY (task_id) REFERENCES tasks(id)
                    )
                """
                )

                conn.commit()
                logger.info(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def get_current_timestamp(self) -> datetime:
        """获取当前时间戳"""
        return datetime.now()
