from typing import Dict, List, Optional, Any
from datetime import datetime
from common.utils.logger import log_manager
from .base import DatabaseBase

# 获取日志记录器
logger = log_manager.get_logger(__name__)


class VersionDB(DatabaseBase):
    """版本数据库操作类"""

    def add_version(
        self,
        model_id: int,
        version: str,
        file_path: str,
        file_size: int,
        file_hash: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """添加版本信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = self.get_current_timestamp()

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

                conn.commit()
                logger.info(f"成功添加版本: model_id={model_id}, version={version}")
                return version_id
        except Exception as e:
            logger.error(f"添加版本失败: {str(e)}")
            return None

    def get_version(self, version_id: int) -> Optional[Dict[str, Any]]:
        """获取版本信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        v.id,
                        v.model_id,
                        v.version,
                        v.file_path,
                        v.file_size,
                        v.file_hash,
                        v.parameters,
                        v.created_at,
                        v.updated_at,
                        m.name as model_name,
                        m.model_type,
                        GROUP_CONCAT(t.name) as task_types
                    FROM versions v
                    JOIN models m ON v.model_id = m.id
                    LEFT JOIN version_tasks vt ON v.id = vt.version_id
                    LEFT JOIN tasks t ON vt.task_id = t.id
                    WHERE v.id = ?
                    GROUP BY v.id
                    """,
                    (version_id,),
                )
                row = cursor.fetchone()

                if not row:
                    logger.warning(f"未找到版本: ID={version_id}")
                    return None

                return {
                    "id": row[0],
                    "model_id": row[1],
                    "version": row[2],
                    "file_path": row[3],
                    "file_size": row[4],
                    "file_hash": row[5],
                    "parameters": eval(row[6]) if row[6] else None,
                    "created_at": row[7],
                    "updated_at": row[8],
                    "model_name": row[9],
                    "model_type": row[10],
                    "task_types": row[11].split(",") if row[11] else [],
                }
        except Exception as e:
            logger.error(f"获取版本信息失败: {str(e)}")
            return None

    def get_model_versions(self, model_id: int) -> List[Dict[str, Any]]:
        """获取模型的所有版本"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        v.id,
                        v.version,
                        v.file_path,
                        v.file_size,
                        v.file_hash,
                        v.parameters,
                        v.created_at,
                        v.updated_at,
                        GROUP_CONCAT(t.name) as task_types
                    FROM versions v
                    LEFT JOIN version_tasks vt ON v.id = vt.version_id
                    LEFT JOIN tasks t ON vt.task_id = t.id
                    WHERE v.model_id = ?
                    GROUP BY v.id
                    ORDER BY v.created_at DESC
                    """,
                    (model_id,),
                )
                rows = cursor.fetchall()

                return [
                    {
                        "id": row[0],
                        "version": row[1],
                        "file_path": row[2],
                        "file_size": row[3],
                        "file_hash": row[4],
                        "parameters": eval(row[5]) if row[5] else None,
                        "created_at": row[6],
                        "updated_at": row[7],
                        "task_types": row[8].split(",") if row[8] else [],
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"获取模型版本列表失败: {str(e)}")
            return []

    def update_version_parameters(
        self, version_id: int, parameters: Dict[str, Any]
    ) -> bool:
        """更新版本参数"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE versions 
                    SET parameters = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (str(parameters), self.get_current_timestamp(), version_id),
                )
                conn.commit()
                logger.info(f"成功更新版本参数: ID={version_id}")
                return True
        except Exception as e:
            logger.error(f"更新版本参数失败: {str(e)}")
            return False

    def delete_version_by_id(self, version_id: int) -> bool:
        """删除版本"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 1. 删除版本-任务关联
                cursor.execute(
                    "DELETE FROM version_tasks WHERE version_id = ?", (version_id,)
                )

                # 2. 删除版本信息
                cursor.execute("DELETE FROM versions WHERE id = ?", (version_id,))

                conn.commit()
                logger.info(f"成功删除版本: ID={version_id}")
                return True
        except Exception as e:
            logger.error(f"删除版本失败: {str(e)}")
            return False

    def add_version_task(self, version_id: int, task_id: int) -> bool:
        """添加版本-任务关联"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = self.get_current_timestamp()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO version_tasks (version_id, task_id, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (version_id, task_id, now),
                )

                conn.commit()
                logger.info(
                    f"成功添加版本-任务关联: version_id={version_id}, task_id={task_id}"
                )
                return True
        except Exception as e:
            logger.error(f"添加版本-任务关联失败: {str(e)}")
            return False

    def remove_version_task(self, version_id: int, task_id: int) -> bool:
        """移除版本-任务关联"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "DELETE FROM version_tasks WHERE version_id = ? AND task_id = ?",
                    (version_id, task_id),
                )

                conn.commit()
                logger.info(
                    f"成功移除版本-任务关联: version_id={version_id}, task_id={task_id}"
                )
                return True
        except Exception as e:
            logger.error(f"移除版本-任务关联失败: {str(e)}")
            return False
