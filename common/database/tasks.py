from typing import Dict, List, Optional, Any
from datetime import datetime
from common.utils.logger import log_manager
from .base import DatabaseBase

# 获取日志记录器
logger = log_manager.get_logger(__name__)


class TaskDB(DatabaseBase):
    """任务数据库操作类"""

    def __init__(self, db_path: str = "models.db"):
        super().__init__(db_path)
        self._init_default_tasks()

    def _init_default_tasks(self):
        """初始化默认任务类型"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 插入默认任务类型
                default_tasks = [
                    ("detect", "目标检测任务"),
                    ("classify", "图像分类任务"),
                ]
                cursor.execute("SELECT COUNT(*) FROM tasks")
                if cursor.fetchone()[0] == 0:
                    now = self.get_current_timestamp()
                    cursor.executemany(
                        """
                        INSERT INTO tasks (name, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        [(name, desc, now, now) for name, desc in default_tasks],
                    )
                    conn.commit()
                    logger.info("成功初始化默认任务类型")
        except Exception as e:
            logger.error(f"初始化默认任务类型失败: {str(e)}")
            raise

    def get_task_id(self, task_name: str) -> Optional[int]:
        """获取任务ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM tasks WHERE name = ?", (task_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"获取任务ID失败: {str(e)}")
            return None

    def get_task_name(self, task_id: int) -> Optional[str]:
        """获取任务名称"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM tasks WHERE id = ?", (task_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"获取任务名称失败: {str(e)}")
            return None

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务类型"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, name, description, created_at, updated_at
                    FROM tasks
                    ORDER BY id
                    """
                )
                rows = cursor.fetchall()

                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "description": row[2],
                        "created_at": row[3],
                        "updated_at": row[4],
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"获取所有任务类型失败: {str(e)}")
            return []

    def add_task(self, name: str, description: Optional[str] = None) -> bool:
        """添加新任务类型"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = self.get_current_timestamp()

                cursor.execute(
                    """
                    INSERT INTO tasks (name, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, description, now, now),
                )

                conn.commit()
                logger.info(f"成功添加任务类型: {name}")
                return True
        except Exception as e:
            logger.error(f"添加任务类型失败: {str(e)}")
            return False

    def delete_task(self, task_id: int) -> bool:
        """删除任务类型"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 检查是否有版本关联
                cursor.execute(
                    "SELECT COUNT(*) FROM version_tasks WHERE task_id = ?", (task_id,)
                )
                if cursor.fetchone()[0] > 0:
                    logger.warning(f"无法删除任务类型 {task_id}: 存在关联的版本")
                    return False

                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                logger.info(f"成功删除任务类型: ID={task_id}")
                return True
        except Exception as e:
            logger.error(f"删除任务类型失败: {str(e)}")
            return False
