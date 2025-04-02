import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from common.utils.logger import log_manager
from config.app_config import Config

# 获取日志记录器
logger = log_manager.get_logger(__name__)


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
                resnet_versions = []

                for version, model_type in rows:
                    if model_type == "detect":
                        detect_versions.append(version)
                    elif model_type == "classify":
                        classify_versions.append(version)
                    elif model_type == "resnet":
                        resnet_versions.append(version)

                return {
                    "detect": detect_versions,
                    "classify": classify_versions,
                    "resnet": resnet_versions,
                }
        except Exception as e:
            logger.error(f"获取所有模型版本失败: {str(e)}")
            return {"detect": [], "classify": [], "resnet": []}

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

    def delete_model_by_id(self, model_id: int) -> bool:
        """
        根据ID删除模型元数据

        Args:
            model_id: 模型ID

        Returns:
            bool: 删除是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 先获取模型信息用于日志
                cursor.execute(
                    """
                    SELECT version, model_type FROM model_metadata 
                    WHERE id = ?
                """,
                    (model_id,),
                )
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"未找到ID为 {model_id} 的模型")
                    return False

                # 删除模型
                cursor.execute(
                    """
                    DELETE FROM model_metadata 
                    WHERE id = ?
                """,
                    (model_id,),
                )
                conn.commit()
                logger.info(
                    f"成功删除模型元数据: ID={model_id}, 版本={row[0]}, 类型={row[1]}"
                )
                return True
        except Exception as e:
            logger.error(f"删除模型元数据失败: {str(e)}")
            return False

    def get_model_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取模型元数据

        Args:
            model_id: 模型ID

        Returns:
            Optional[Dict[str, Any]]: 模型元数据，如果不存在则返回None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM model_metadata 
                    WHERE id = ?
                """,
                    (model_id,),
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

    def update_model_parameters(
        self, model_id: int, parameters: Dict[str, Any]
    ) -> bool:
        """
        更新模型参数

        Args:
            model_id: 模型ID
            parameters: 要更新的参数字典

        Returns:
            bool: 更新是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 先获取当前参数
                cursor.execute(
                    """
                    SELECT parameters FROM model_metadata 
                    WHERE id = ?
                """,
                    (model_id,),
                )
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"未找到ID为 {model_id} 的模型")
                    return False

                # 更新参数
                current_params = eval(row[0]) if row[0] else {}
                current_params.update(parameters)
                cursor.execute(
                    """
                    UPDATE model_metadata 
                    SET parameters = ?, updated_at = ?
                    WHERE id = ?
                """,
                    (str(current_params), datetime.now(), model_id),
                )
                conn.commit()
                logger.info(f"成功更新模型参数: ID={model_id}, 参数={parameters}")
                return True
        except Exception as e:
            logger.error(f"更新模型参数失败: {str(e)}")
            return False
