import time
import torch
import onnxruntime
import psutil
from flask import current_app
from common.utils.response import ApiResponse
from common.utils.redis_utils import RedisClient
from common.utils.logger import log_manager
from . import health_bp

# 获取日志记录器
logger = log_manager.get_logger(__name__)


def check_redis_connection():
    """检查Redis连接状态"""
    try:
        redis_client = RedisClient.get_instance()
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis连接检查失败: {str(e)}")
        return False


def check_gpu_status():
    """检查GPU状态"""
    try:
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            gpu_count = torch.cuda.device_count()
            gpu_memory = []
            for i in range(gpu_count):
                gpu_memory.append(torch.cuda.get_device_properties(i).total_memory)
            return {"available": True, "count": gpu_count, "memory": gpu_memory}
        return {"available": False}
    except Exception as e:
        logger.error(f"GPU状态检查失败: {str(e)}")
        return {"available": False, "error": str(e)}


def check_onnx_runtime():
    """检查ONNX Runtime状态"""
    try:
        version = onnxruntime.__version__
        providers = onnxruntime.get_available_providers()
        gpu_available = "CUDAExecutionProvider" in providers
        return {
            "version": version,
            "gpu_available": gpu_available,
            "providers": providers,
        }
    except Exception as e:
        logger.error(f"ONNX Runtime检查失败: {str(e)}")
        return {"error": str(e)}


def check_system_resources():
    """检查系统资源使用情况"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
            },
            "disk": {"total": disk.total, "free": disk.free, "percent": disk.percent},
        }
    except Exception as e:
        logger.error(f"系统资源检查失败: {str(e)}")
        return {"error": str(e)}


@health_bp.route("/health")
def health_check():
    """健康检查接口"""
    try:
        # 检查各个组件状态
        redis_status = check_redis_connection()
        gpu_status = check_gpu_status()
        onnx_status = check_onnx_runtime()
        system_status = check_system_resources()

        # 综合状态
        status = {
            "status": "healthy" if redis_status else "unhealthy",
            "timestamp": time.time(),
            "components": {
                "redis": redis_status,
                "gpu": gpu_status,
                "onnx": onnx_status,
                "system": system_status,
            },
        }

        # 记录健康检查结果
        logger.info(f"健康检查结果: {status}")

        return ApiResponse.success(data=status)
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return ApiResponse.error(message=f"健康检查失败: {str(e)}", code=500)
