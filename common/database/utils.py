from typing import Dict, List, Any
from common.utils.logger import log_manager
from .base import DatabaseBase

# 获取日志记录器
logger = log_manager.get_logger(__name__)


class DatabaseUtils(DatabaseBase):
    """数据库工具类"""

    def verify_model_data(self) -> bool:
        """验证数据库中的模型数据完整性"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 检查模型表
                cursor.execute("SELECT * FROM models")
                models = cursor.fetchall()
                logger.info(f"模型表中有 {len(models)} 条记录")
                for model in models:
                    logger.info(f"模型记录: {model}")

                # 检查版本表
                cursor.execute("SELECT * FROM versions")
                versions = cursor.fetchall()
                logger.info(f"版本表中有 {len(versions)} 条记录")
                for version in versions:
                    logger.info(f"版本记录: {version}")

                # 检查任务表
                cursor.execute("SELECT * FROM tasks")
                tasks = cursor.fetchall()
                logger.info(f"任务表中有 {len(tasks)} 条记录")
                for task in tasks:
                    logger.info(f"任务记录: {task}")

                # 检查版本-任务关联表
                cursor.execute("SELECT * FROM version_tasks")
                version_tasks = cursor.fetchall()
                logger.info(f"版本-任务关联表中有 {len(version_tasks)} 条记录")
                for vt in version_tasks:
                    logger.info(f"版本-任务关联记录: {vt}")

                # 检查数据完整性
                cursor.execute(
                    """
                    SELECT m.name, v.version, COUNT(vt.task_id) as task_count
                    FROM models m
                    JOIN versions v ON m.id = v.model_id
                    LEFT JOIN version_tasks vt ON v.id = vt.version_id
                    GROUP BY m.id, v.id
                """
                )
                model_stats = cursor.fetchall()
                logger.info("模型统计信息:")
                for stat in model_stats:
                    logger.info(f"模型: {stat[0]}-{stat[1]}, 任务数量: {stat[2]}")

                return True
        except Exception as e:
            logger.error(f"验证模型数据失败: {str(e)}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # 获取各表记录数
                tables = ["models", "versions", "tasks", "version_tasks"]
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]

                # 获取模型类型统计
                cursor.execute(
                    """
                    SELECT model_type, COUNT(*) as count
                    FROM models
                    GROUP BY model_type
                    """
                )
                stats["model_types"] = dict(cursor.fetchall())

                # 获取任务类型统计
                cursor.execute(
                    """
                    SELECT t.name, COUNT(vt.version_id) as count
                    FROM tasks t
                    LEFT JOIN version_tasks vt ON t.id = vt.task_id
                    GROUP BY t.id
                    """
                )
                stats["task_types"] = dict(cursor.fetchall())

                # 获取版本统计
                cursor.execute(
                    """
                    SELECT m.name, COUNT(v.id) as version_count
                    FROM models m
                    LEFT JOIN versions v ON m.id = v.model_id
                    GROUP BY m.id
                    """
                )
                stats["model_versions"] = dict(cursor.fetchall())

                return stats
        except Exception as e:
            logger.error(f"获取数据库统计信息失败: {str(e)}")
            return {}

    def cleanup_orphaned_data(self) -> Dict[str, int]:
        """清理孤立数据"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cleanup_stats = {}

                # 清理孤立的版本-任务关联
                cursor.execute(
                    """
                    DELETE FROM version_tasks
                    WHERE version_id NOT IN (SELECT id FROM versions)
                    OR task_id NOT IN (SELECT id FROM tasks)
                    """
                )
                cleanup_stats["orphaned_version_tasks"] = cursor.rowcount

                # 清理孤立的版本
                cursor.execute(
                    """
                    DELETE FROM versions
                    WHERE model_id NOT IN (SELECT id FROM models)
                    """
                )
                cleanup_stats["orphaned_versions"] = cursor.rowcount

                conn.commit()
                logger.info(f"清理孤立数据完成: {cleanup_stats}")
                return cleanup_stats
        except Exception as e:
            logger.error(f"清理孤立数据失败: {str(e)}")
            return {}
