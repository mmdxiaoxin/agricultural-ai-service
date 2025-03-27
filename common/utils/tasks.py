import logging
from celery import Celery
from common.utils.redis_utils import RedisClient
from services.ai_service import AIService

logger = logging.getLogger(__name__)

# 创建Celery实例
celery = Celery("agricultural_ai")
celery.config_from_object("celery_config")

# 创建AI服务实例
ai_service = AIService()


@celery.task(name="tasks.detect", bind=True)
def detect_task(self, version: str, image_data: bytes):
    """目标检测任务"""
    try:
        # 调用服务层进行推理
        result = ai_service.detect(version, image_data)
        if result is None:
            raise Exception(f"未找到模型版本: {version}")

        # 缓存结果
        cache_key = f"detect:{version}:{self.request.id}"
        RedisClient.set_cache(cache_key, result, ttl=3600)  # 缓存1小时

        return result
    except Exception as e:
        logger.error(f"目标检测任务失败: {str(e)}")
        raise


@celery.task(name="tasks.classify", bind=True)
def classify_task(self, version: str, image_data: bytes):
    """图像分类任务"""
    try:
        # 调用服务层进行推理
        result = ai_service.classify(version, image_data)
        if result is None:
            raise Exception(f"未找到模型版本: {version}")

        # 缓存结果
        cache_key = f"classify:{version}:{self.request.id}"
        RedisClient.set_cache(cache_key, result, ttl=3600)  # 缓存1小时

        return result
    except Exception as e:
        logger.error(f"图像分类任务失败: {str(e)}")
        raise
