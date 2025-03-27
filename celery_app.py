from celery import Celery
from config import AppConfig, CeleryConfig


def create_celery_app(app=None):
    """创建Celery实例"""
    celery = Celery(
        app.import_name if app else "agricultural_ai",
        broker=CeleryConfig.broker_url,
        backend=CeleryConfig.result_backend,
    )

    # 配置Celery
    celery.conf.update(CeleryConfig.__dict__)

    # 如果提供了Flask应用，设置任务上下文
    if app is not None:

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


# 创建默认的celery实例
celery = create_celery_app()
