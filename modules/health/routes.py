import time
import torch
import onnxruntime
import psutil
import os
import multiprocessing
from flask import current_app
from common.utils.response import ApiResponse
from common.utils.redis_utils import RedisClient
from common.utils.logger import log_manager
from common.database.utils import DatabaseUtils
from celery_app import create_celery_app
from . import health_bp

# 获取日志记录器
logger = log_manager.get_logger(__name__)

# 资源使用阈值
RESOURCE_THRESHOLDS = {
    "cpu_percent": 80,  # CPU使用率阈值
    "memory_percent": 80,  # 内存使用率阈值
    "disk_percent": 80,  # 磁盘使用率阈值
}


def check_redis_connection():
    """检查Redis连接状态"""
    try:
        redis_client = RedisClient.get_instance()
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis连接检查失败: {str(e)}")
        return False


def check_database_connection():
    """检查数据库连接状态"""
    try:
        db_utils = DatabaseUtils()
        db_utils.verify_model_data()
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {str(e)}")
        return False


def check_celery_status():
    """检查Celery状态"""
    try:
        app = current_app._get_current_object()
        celery = create_celery_app(app)
        inspect = celery.control.inspect()
        stats = inspect.stats()
        return {"available": bool(stats), "stats": stats}
    except Exception as e:
        logger.error(f"Celery状态检查失败: {str(e)}")
        return {"available": False, "error": str(e)}


def _check_gpu():
    """在独立进程中检查GPU状态"""
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


def check_gpu_status():
    """检查GPU状态"""
    try:
        # 检查是否在Docker环境中运行
        is_docker = os.path.exists("/.dockerenv")

        if os.name == "nt":  # Windows系统直接检查
            gpu_available = torch.cuda.is_available()
            if gpu_available:
                gpu_count = torch.cuda.device_count()
                gpu_memory = []
                for i in range(gpu_count):
                    gpu_memory.append(torch.cuda.get_device_properties(i).total_memory)
                return {"available": True, "count": gpu_count, "memory": gpu_memory}
            return {"available": False}
        else:  # Linux系统
            if is_docker:
                # Docker环境中使用环境变量检查GPU
                nvidia_smi = (
                    os.popen(
                        "nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits"
                    )
                    .read()
                    .strip()
                )
                if nvidia_smi:
                    gpu_memory = [int(x) for x in nvidia_smi.split("\n")]
                    return {
                        "available": True,
                        "count": len(gpu_memory),
                        "memory": gpu_memory,
                    }
                return {"available": False}
            else:
                # 非Docker环境使用独立进程
                import torch.multiprocessing as torch_mp

                torch_mp.set_start_method("spawn", force=True)
                multiprocessing.set_start_method("spawn", force=True)

                with multiprocessing.Pool(1) as pool:
                    result = pool.apply(_check_gpu)
                return result
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

        # 检查是否超过阈值
        warnings = []
        if cpu_percent > RESOURCE_THRESHOLDS["cpu_percent"]:
            warnings.append(f"CPU使用率过高: {cpu_percent}%")
        if memory.percent > RESOURCE_THRESHOLDS["memory_percent"]:
            warnings.append(f"内存使用率过高: {memory.percent}%")
        if disk.percent > RESOURCE_THRESHOLDS["disk_percent"]:
            warnings.append(f"磁盘使用率过高: {disk.percent}%")

        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent,
            },
            "warnings": warnings,
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
        db_status = check_database_connection()
        celery_status = check_celery_status()
        gpu_status = check_gpu_status()
        onnx_status = check_onnx_runtime()
        system_status = check_system_resources()

        # 综合状态判断
        is_healthy = all(
            [
                redis_status,
                db_status,
                celery_status.get("available", False),
                gpu_status.get("available", False),
                onnx_status.get("gpu_available", False),
            ]
        )

        # 检查系统资源警告
        system_warnings = system_status.get("warnings", [])
        if system_warnings:
            logger.warning(f"系统资源警告: {system_warnings}")

        # 综合状态
        status = {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": time.time(),
            "components": {
                "redis": redis_status,
                "database": db_status,
                "celery": celery_status,
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
