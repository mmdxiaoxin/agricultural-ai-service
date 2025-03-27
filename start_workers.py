from celery import Celery
from config.celery_config import Config
from config.app_config import Config as AppConfig

# 初始化配置
AppConfig.init_app(None)

# 创建Celery实例
celery = Celery("agricultural_ai")
celery.config_from_object(Config)  # 使用模块路径字符串

if __name__ == "__main__":
    # 启动工作进程
    argv = [
        "worker",
        "--loglevel=INFO",
        "--pool=solo",  # Windows下使用solo池
        "--concurrency=2",  # 并发worker数
        "--hostname=worker@%h",  # worker主机名
        "--queues=detect,classify",  # 指定要处理的队列
    ]
    celery.worker_main(argv)
