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

                # 创建模型基本信息表
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS models (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        model_type TEXT NOT NULL,  -- yolo, resnet等
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

                # 插入默认任务类型
                default_tasks = [
                    ("detect", "目标检测任务"),
                    ("classify", "图像分类任务"),
                ]
                cursor.execute("SELECT COUNT(*) FROM tasks")
                if cursor.fetchone()[0] == 0:
                    now = datetime.now()
                    cursor.executemany(
                        """
                        INSERT INTO tasks (name, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        [(name, desc, now, now) for name, desc in default_tasks],
                    )

                conn.commit()
                logger.info(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise

    def add_model(
        self,
        name: str,
        version: str,
        task_type: str,
        file_path: str,
        file_size: int,
        file_hash: str,
        parameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> bool:
        """添加模型及其版本信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now()

                # 从名称中提取模型类型
                model_type = name.split("_")[0].lower()  # yolo或resnet

                # 1. 添加或获取模型基本信息
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO models 
                    (name, model_type, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, model_type, description, now, now),
                )

                # 获取模型ID
                cursor.execute("SELECT id FROM models WHERE name = ?", (name,))
                model_id = cursor.fetchone()[0]

                # 2. 添加版本信息
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO versions 
                    (model_id, version, file_path, file_size, file_hash, 
                     parameters, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        model_id,
                        version,
                        file_path,
                        file_size,
                        file_hash,
                        str(parameters) if parameters else None,
                        now,
                        now,
                    ),
                )

                # 获取版本ID
                cursor.execute(
                    "SELECT id FROM versions WHERE model_id = ? AND version = ?",
                    (model_id, version),
                )
                version_id = cursor.fetchone()[0]

                # 3. 获取任务类型ID
                cursor.execute("SELECT id FROM tasks WHERE name = ?", (task_type,))
                task_id = cursor.fetchone()[0]

                # 4. 添加版本-任务关联
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO version_tasks (version_id, task_id, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (version_id, task_id, now),
                )

                conn.commit()
                logger.info(f"成功添加模型: {name}-{version}-{task_type}")
                return True
        except Exception as e:
            logger.error(f"添加模型失败: {str(e)}")
            return False

    def get_model(self, name: str, version: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT m.*, v.*, GROUP_CONCAT(t.name) as task_types
                    FROM models m
                    JOIN versions v ON m.id = v.model_id
                    LEFT JOIN version_tasks vt ON v.id = vt.version_id
                    LEFT JOIN tasks t ON vt.task_id = t.id
                    WHERE m.name = ? AND v.version = ?
                    GROUP BY m.id, v.id
                    """,
                    (name, version),
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "model_id": row[0],
                        "name": row[1],
                        "model_type": row[2],
                        "description": row[3],
                        "version_id": row[6],
                        "version": row[8],
                        "file_path": row[9],
                        "file_size": row[10],
                        "file_hash": row[11],
                        "parameters": eval(row[12]) if row[12] else None,
                        "task_types": row[17].split(",") if row[17] else [],
                        "created_at": row[13],
                        "updated_at": row[14],
                    }
                return None
        except Exception as e:
            logger.error(f"获取模型信息失败: {str(e)}")
            return None

    def get_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有模型信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        m.name, 
                        m.model_type,
                        m.description, 
                        v.version, 
                        GROUP_CONCAT(t.name) as task_types
                    FROM models m
                    JOIN versions v ON m.id = v.model_id
                    LEFT JOIN version_tasks vt ON v.id = vt.version_id
                    LEFT JOIN tasks t ON vt.task_id = t.id
                    GROUP BY m.id, v.id
                    """
                )
                rows = cursor.fetchall()

                result = {}
                for name, model_type, description, version, task_types in rows:
                    if name not in result:
                        result[name] = []
                    result[name].append(
                        {
                            "version": version,
                            "model_type": model_type,
                            "task_types": task_types.split(",") if task_types else [],
                            "description": description,
                        }
                    )
                return result
        except Exception as e:
            logger.error(f"获取所有模型信息失败: {str(e)}")
            return {}

    def delete_model(self, name: str, version: str) -> bool:
        """删除模型版本"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 1. 获取版本ID
                cursor.execute(
                    """
                    SELECT v.id FROM versions v
                    JOIN models m ON v.model_id = m.id
                    WHERE m.name = ? AND v.version = ?
                    """,
                    (name, version),
                )
                version_id = cursor.fetchone()
                if not version_id:
                    logger.warning(f"未找到模型版本: {name}-{version}")
                    return False
                version_id = version_id[0]

                # 2. 删除版本-任务关联
                cursor.execute(
                    "DELETE FROM version_tasks WHERE version_id = ?", (version_id,)
                )

                # 3. 删除版本信息
                cursor.execute("DELETE FROM versions WHERE id = ?", (version_id,))

                # 4. 检查是否还有其他版本
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM versions v
                    JOIN models m ON v.model_id = m.id
                    WHERE m.name = ?
                    """,
                    (name,),
                )
                remaining_versions = cursor.fetchone()[0]

                # 5. 如果没有其他版本，删除模型信息
                if remaining_versions == 0:
                    cursor.execute("DELETE FROM models WHERE name = ?", (name,))

                conn.commit()
                logger.info(f"成功删除模型版本: {name}-{version}")
                return True
        except Exception as e:
            logger.error(f"删除模型版本失败: {str(e)}")
            return False

    def update_model_parameters(
        self, name: str, version: str, parameters: Dict[str, Any]
    ) -> bool:
        """更新模型参数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE versions 
                    SET parameters = ?, updated_at = ?
                    WHERE id = (
                        SELECT v.id FROM versions v
                        JOIN models m ON v.model_id = m.id
                        WHERE m.name = ? AND v.version = ?
                    )
                    """,
                    (str(parameters), datetime.now(), name, version),
                )
                conn.commit()
                logger.info(f"成功更新模型参数: {name}-{version}")
                return True
        except Exception as e:
            logger.error(f"更新模型参数失败: {str(e)}")
            return False
