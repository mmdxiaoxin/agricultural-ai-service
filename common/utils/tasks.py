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
            # 检查模型是否存在
            model = initializer.model_manager.get_detect_model(version)
            if model is None:
                raise Exception(f"未找到检测模型版本: {version}")
            else:
                raise Exception("目标检测推理失败，请检查模型状态或图片数据")

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
            # 检查模型是否存在
            model = initializer.model_manager.get_classify_model(version)
            if model is None:
                raise Exception(f"未找到分类模型版本: {version}")
            else:
                raise Exception("图像分类推理失败，请检查模型状态或图片数据")

        # 缓存结果，直接使用task_id
        cache_key = f"classify:{self.request.id}"
        initializer.redis_client.set_cache(cache_key, result, ttl=3600)  # 缓存1小时

        return result
    except Exception as e:
        logger.error(f"图像分类任务失败: {str(e)}")
        raise
