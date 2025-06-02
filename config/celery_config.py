from config.app_config import Config as AppConfig
import os


class Config:
    # Celery配置
    broker_url = (
        f"redis://{AppConfig.REDIS_HOST}:{AppConfig.REDIS_PORT}/{AppConfig.REDIS_DB}"
    )
    result_backend = (
        f"redis://{AppConfig.REDIS_HOST}:{AppConfig.REDIS_PORT}/{AppConfig.REDIS_DB}"
    )

    # 连接重试配置
    broker_connection_retry = True
    broker_connection_retry_on_startup = True
    broker_connection_max_retries = 10

    # 日志配置
    worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
    worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s"
    worker_redirect_stdouts = True
    worker_redirect_stdouts_level = "WARNING"

    # 任务配置
    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]
    timezone = "Asia/Shanghai"
    enable_utc = True

    # 任务执行配置
    task_track_started = True
    task_time_limit = 300  # 5分钟超时
    task_soft_time_limit = 240  # 4分钟软超时
    max_request_size = 10485760  # 10MB

    # 工作进程配置
    worker_prefetch_multiplier = 4  # 每个工作进程一次可以处理4个任务
    worker_max_tasks_per_child = 1000  # 处理1000个任务后重启工作进程，防止内存泄漏
    worker_max_memory_per_child = 1024000  # 1GB内存限制

    # 进程池配置 - 根据操作系统选择
    worker_pool = (
        "solo" if os.name == "nt" else "prefork"
    )  # Windows使用solo，Linux使用prefork
    worker_pool_restarts = True  # 允许工作进程重启
    worker_pool_restart_interval = 30  # 每30秒检查一次是否需要重启

    # 任务路由
    task_routes = {
        "tasks.detect": {"queue": "detect", "routing_key": "detect"},
        "tasks.classify": {"queue": "classify", "routing_key": "classify"},
    }

    # 任务队列配置
    task_queues = {
        "detect": {
            "exchange": "detect",
            "routing_key": "detect",
            "queue_arguments": {"x-max-priority": 10},
        },
        "classify": {
            "exchange": "classify",
            "routing_key": "classify",
            "queue_arguments": {"x-max-priority": 10},
        },
    }
