import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)


class Database:
    """数据库操作类"""

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
                # 创建模型元数据表
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS model_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT NOT NULL,
                        model_type TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        file_hash TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        parameters TEXT,
                        UNIQUE(version, model_type)
                    )
                """
                )
                conn.commit()
                logger.info(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise

    def add_model(
        self,
        version: str,
        model_type: str,
        file_path: str,
        file_size: int,
        file_hash: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """添加模型元数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO model_metadata 
                    (version, model_type, file_path, file_size, file_hash, 
                     created_at, updated_at, parameters)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        version,
                        model_type,
                        file_path,
                        file_size,
                        file_hash,
                        now,
                        now,
                        str(parameters) if parameters else None,
                    ),
                )
                conn.commit()
                logger.info(f"成功添加模型元数据: {version}-{model_type}")
                return True
        except Exception as e:
            logger.error(f"添加模型元数据失败: {str(e)}")
            return False

    def get_model(self, version: str, model_type: str) -> Optional[Dict[str, Any]]:
        """获取模型元数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM model_metadata 
                    WHERE version = ? AND model_type = ?
                """,
                    (version, model_type),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "version": row[1],
                        "model_type": row[2],
                        "file_path": row[3],
                        "file_size": row[4],
                        "file_hash": row[5],
                        "created_at": row[6],
                        "updated_at": row[7],
                        "parameters": eval(row[8]) if row[8] else None,
                    }
                return None
        except Exception as e:
            logger.error(f"获取模型元数据失败: {str(e)}")
            return None

    def get_all_models(self) -> Dict[str, List[str]]:
        """获取所有可用的模型版本"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version, model_type FROM model_metadata")
                rows = cursor.fetchall()

                detect_versions = []
                classify_versions = []

                for version, model_type in rows:
                    if model_type == "detect":
                        detect_versions.append(version)
                    elif model_type == "classify":
                        classify_versions.append(version)

                return {"detect": detect_versions, "classify": classify_versions}
        except Exception as e:
            logger.error(f"获取所有模型版本失败: {str(e)}")
            return {"detect": [], "classify": []}

    def delete_model(self, version: str, model_type: str) -> bool:
        """删除模型元数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM model_metadata 
                    WHERE version = ? AND model_type = ?
                """,
                    (version, model_type),
                )
                conn.commit()
                logger.info(f"成功删除模型元数据: {version}-{model_type}")
                return True
        except Exception as e:
            logger.error(f"删除模型元数据失败: {str(e)}")
            return False
