from celery_app import celery
from common.init import initializer
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)


@celery.task(name="tasks.detect", bind=True)
def detect_task(self, version: str, image_data: bytes):
    """目标检测任务"""
    try:
        # 调用服务层进行推理
        result = initializer.ai_service.detect(version, image_data)
        if result is None:
            raise Exception(f"未找到模型版本: {version}")

        # 缓存结果，直接使用task_id
        cache_key = f"detect:{self.request.id}"
        initializer.redis_client.set_cache(cache_key, result, ttl=3600)  # 缓存1小时

        return result
    except Exception as e:
        logger.error(f"目标检测任务失败: {str(e)}")
        raise


@celery.task(name="tasks.classify", bind=True)
def classify_task(self, version: str, image_data: bytes):
    """图像分类任务"""
    try:
        # 调用服务层进行推理
        result = initializer.ai_service.classify(version, image_data)
        if result is None:
            raise Exception(f"未找到模型版本: {version}")

        # 缓存结果，直接使用task_id
        cache_key = f"classify:{self.request.id}"
        initializer.redis_client.set_cache(cache_key, result, ttl=3600)  # 缓存1小时

        return result
    except Exception as e:
        logger.error(f"图像分类任务失败: {str(e)}")
        raise
