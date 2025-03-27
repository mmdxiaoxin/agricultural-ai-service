from celery import Celery

# 创建Celery实例
celery = Celery("agricultural_ai")
celery.config_from_object("celery_config")

if __name__ == "__main__":
    # 启动工作进程
    celery.start()
