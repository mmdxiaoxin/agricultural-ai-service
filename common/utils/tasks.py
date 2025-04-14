from celery_app import celery
from common.init import initializer
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)


@celery.task(name="tasks.detect", bind=True)
def detect_task(self, model_name: str, version: str, image_data: bytes):
    """目标检测任务"""
    try:
        # 直接调用服务层进行推理
        result = initializer.ai_service.detect(model_name, version, image_data)
        if result is None:
            raise Exception("目标检测推理失败，请检查模型状态或图片数据")

        # 缓存结果，直接使用task_id
        cache_key = f"detect:{self.request.id}"
        initializer.redis_client.set_cache(cache_key, result, ttl=3600)  # 缓存1小时

        return result
    except Exception as e:
        logger.error(f"目标检测任务失败: {str(e)}")
        raise


@celery.task(name="tasks.classify", bind=True)
def classify_task(self, model_name: str, version: str, image_data: bytes):
    """图像分类任务"""
    try:
        # 直接调用服务层进行推理
        result = initializer.ai_service.classify(model_name, version, image_data)
        if result is None:
            raise Exception("图像分类推理失败，请检查模型状态或图片数据")

        # 缓存结果，直接使用task_id
        cache_key = f"classify:{self.request.id}"
        initializer.redis_client.set_cache(cache_key, result, ttl=3600)  # 缓存1小时

        return result
    except Exception as e:
        logger.error(f"图像分类任务失败: {str(e)}")
        raise
