from config.app_config import Config as AppConfig


class Config:
    # Celery配置
    broker_url = (
        f"redis://{AppConfig.REDIS_HOST}:{AppConfig.REDIS_PORT}/{AppConfig.REDIS_DB}"
    )
    result_backend = (
        f"redis://{AppConfig.REDIS_HOST}:{AppConfig.REDIS_PORT}/{AppConfig.REDIS_DB}"
    )

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

    # 工作进程配置
    worker_prefetch_multiplier = 1  # 每个工作进程一次只处理一个任务
    worker_max_tasks_per_child = 100  # 处理100个任务后重启工作进程
    worker_max_memory_per_child = 512000  # 512MB内存限制

    # 任务路由
    task_routes = {
        "tasks.detect": {"queue": "detect"},
        "tasks.classify": {"queue": "classify"},
    }
