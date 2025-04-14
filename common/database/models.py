from typing import Dict, List, Optional, Any
from datetime import datetime
from common.utils.logger import log_manager
from .base import DatabaseBase

# 获取日志记录器
logger = log_manager.get_logger(__name__)


class ModelDB(DatabaseBase):
    """模型数据库操作类"""

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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = self.get_current_timestamp()

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
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        m.id as model_id,
                        m.name, 
                        m.model_type,
                        m.description, 
                        m.created_at as model_created_at,
                        m.updated_at as model_updated_at,
                        v.id as version_id,
                        v.version,
                        v.file_path,
                        v.file_size,
                        v.file_hash,
                        v.parameters,
                        v.created_at as version_created_at,
                        v.updated_at as version_updated_at,
                        GROUP_CONCAT(t.name) as task_types
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

                if not row:
                    logger.warning(f"未找到模型: {name}-{version}")
                    return None

                try:
                    # 确保所有必要的字段都存在
                    if len(row) < 15:  # 检查行数据是否完整
                        logger.error(
                            f"模型数据不完整: {name}-{version}, 列数: {len(row)}"
                        )
                        return None

                    return {
                        "model_id": row[0],
                        "name": row[1],
                        "model_type": row[2],
                        "description": row[3],
                        "version_id": row[6],
                        "version": row[7],
                        "file_path": row[8],
                        "file_size": row[9],
                        "file_hash": row[10],
                        "parameters": eval(row[11]) if row[11] else None,
                        "task_types": row[14].split(",") if row[14] else [],
                        "created_at": row[12],
                        "updated_at": row[13],
                    }
                except IndexError as e:
                    logger.error(f"解析模型数据时出错: {str(e)}, 数据: {row}")
                    return None

        except Exception as e:
            logger.error(f"获取模型信息失败: {str(e)}")
            return None

    def get_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有模型信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        m.id as model_id,
                        m.name, 
                        m.model_type,
                        m.description, 
                        v.id as version_id,
                        v.version,
                        v.file_path,
                        v.file_size,
                        v.file_hash,
                        v.parameters,
                        GROUP_CONCAT(t.name) as task_types,
                        v.created_at,
                        v.updated_at
                    FROM models m
                    JOIN versions v ON m.id = v.model_id
                    LEFT JOIN version_tasks vt ON v.id = vt.version_id
                    LEFT JOIN tasks t ON vt.task_id = t.id
                    GROUP BY m.id, v.id
                    """
                )
                rows = cursor.fetchall()

                if not rows:
                    logger.warning("数据库中没有找到任何模型")
                    return {}

                result = {}
                for row in rows:
                    try:
                        name = row[1]  # m.name
                        if name not in result:
                            result[name] = []

                        result[name].append(
                            {
                                "model_id": row[0],
                                "version": row[5],
                                "model_type": row[2],
                                "description": row[3],
                                "version_id": row[4],
                                "file_path": row[6],
                                "file_size": row[7],
                                "file_hash": row[8],
                                "parameters": eval(row[9]) if row[9] else None,
                                "task_types": row[10].split(",") if row[10] else [],
                                "created_at": row[11],
                                "updated_at": row[12],
                            }
                        )
                    except IndexError as e:
                        logger.error(f"解析模型数据时出错: {str(e)}, 数据: {row}")
                        continue

                return result
        except Exception as e:
            logger.error(f"获取所有模型信息失败: {str(e)}")
            return {}

    def delete_model(self, name: str, version: str) -> bool:
        """删除模型版本"""
        try:
            with self.get_connection() as conn:
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

    def delete_model_by_id(self, model_id: int) -> bool:
        """根据ID删除模型"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 1. 获取版本ID
                cursor.execute(
                    """
                    SELECT v.id FROM versions v
                    WHERE v.model_id = ?
                    """,
                    (model_id,),
                )
                version_ids = [row[0] for row in cursor.fetchall()]

                # 2. 删除版本-任务关联
                if version_ids:
                    cursor.execute(
                        "DELETE FROM version_tasks WHERE version_id IN ({})".format(
                            ",".join("?" * len(version_ids))
                        ),
                        version_ids,
                    )

                # 3. 删除版本信息
                cursor.execute("DELETE FROM versions WHERE model_id = ?", (model_id,))

                # 4. 删除模型信息
                cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))

                conn.commit()
                logger.info(f"成功删除模型: ID={model_id}")
                return True
        except Exception as e:
            logger.error(f"删除模型失败: {str(e)}")
            return False

    def get_model_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取模型信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT m.*, v.*, GROUP_CONCAT(t.name) as task_types
                    FROM models m
                    JOIN versions v ON m.id = v.model_id
                    LEFT JOIN version_tasks vt ON v.id = vt.version_id
                    LEFT JOIN tasks t ON vt.task_id = t.id
                    WHERE m.id = ?
                    GROUP BY m.id, v.id
                    """,
                    (model_id,),
                )
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"未找到ID为 {model_id} 的模型")
                    return None

                try:
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
                except IndexError as e:
                    logger.error(f"解析模型数据时出错: {str(e)}")
                    return None
        except Exception as e:
            logger.error(f"获取模型信息失败: {str(e)}")
            return None

    def get_model_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """根据文件哈希获取模型信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 
                        m.id as model_id,
                        m.name, 
                        m.model_type,
                        m.description, 
                        m.created_at as model_created_at,
                        m.updated_at as model_updated_at,
                        v.id as version_id,
                        v.version,
                        v.file_path,
                        v.file_size,
                        v.file_hash,
                        v.parameters,
                        v.created_at as version_created_at,
                        v.updated_at as version_updated_at,
                        GROUP_CONCAT(t.name) as task_types
                    FROM models m
                    JOIN versions v ON m.id = v.model_id
                    LEFT JOIN version_tasks vt ON v.id = vt.version_id
                    LEFT JOIN tasks t ON vt.task_id = t.id
                    WHERE v.file_hash = ?
                    GROUP BY m.id, v.id
                    """,
                    (file_hash,),
                )
                row = cursor.fetchone()

                if not row:
                    return None

                try:
                    return {
                        "model_id": row[0],
                        "name": row[1],
                        "model_type": row[2],
                        "description": row[3],
                        "version_id": row[6],
                        "version": row[7],
                        "file_path": row[8],
                        "file_size": row[9],
                        "file_hash": row[10],
                        "parameters": eval(row[11]) if row[11] else None,
                        "task_types": row[14].split(",") if row[14] else [],
                        "created_at": row[12],
                        "updated_at": row[13],
                    }
                except IndexError as e:
                    logger.error(f"解析模型数据时出错: {str(e)}, 数据: {row}")
                    return None

        except Exception as e:
            logger.error(f"获取模型信息失败: {str(e)}")
            return None
