from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 任务等待中
    PROCESSING = "processing"  # 任务处理中
    SUCCESS = "success"  # 任务成功
    FAILURE = "failure"  # 任务失败

    @classmethod
    def from_celery_state(cls, state: str) -> "TaskStatus":
        """从Celery状态转换为任务状态"""
        state_map = {
            "PENDING": cls.PENDING,
            "PROGRESS": cls.PROCESSING,
            "STARTED": cls.PROCESSING,
            "SUCCESS": cls.SUCCESS,
            "FAILURE": cls.FAILURE,
        }
        return state_map.get(state, cls.PROCESSING)  # 未知状态默认为处理中
