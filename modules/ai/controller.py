import logging
import shutil
from flask import request
from werkzeug.exceptions import RequestEntityTooLarge
from pathlib import Path
import hashlib

from services.ai_service import AIService
from common.utils.response import ApiResponse, ResponseCode
from config.app_config import Config
from common.models.database import Database
from common.utils.redis_utils import RedisClient
from common.utils.tasks import detect_task, classify_task

logger = logging.getLogger(__name__)

# 创建AI服务实例
ai_service = AIService()
# 创建数据库实例
db = Database()


def detect_controller(version: str):
    """
    接收植物图像，进行目标检测推理

    Args:
        version: 模型版本
    """
    try:
        # 检查请求大小
        if request.content_length and not Config.validate_file_size(
            request.content_length
        ):
            return ApiResponse.file_too_large(
                f"文件大小超过限制（最大{Config.MAX_FILE_SIZE // (1024*1024)}MB）"
            )

        if "image" not in request.files:
            return ApiResponse.bad_request("未提供图片文件")

        # 获取图片文件
        image_file = request.files["image"]
        if not image_file.filename:
            return ApiResponse.bad_request("未选择文件")

        # 检查文件类型
        if not Config.validate_file_extension(image_file.filename):
            return ApiResponse.bad_request("不支持的文件类型，仅支持PNG和JPG格式")

        # 读取图片数据
        image_data = image_file.read()

        # 提交异步任务
        task = detect_task.delay(version, image_data)

        # 返回任务ID
        return ApiResponse.success(
            data={
                "task_id": task.id,
                "status": "processing",
                "message": "任务已提交，请稍后查询结果",
            }
        )

    except RequestEntityTooLarge:
        logger.error("请求文件过大")
        return ApiResponse.file_too_large(
            f"文件大小超过限制（最大{Config.MAX_FILE_SIZE // (1024*1024)}MB）"
        )
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def get_detect_result_controller(task_id: str):
    """获取目标检测任务结果"""
    try:
        # 获取任务状态
        task = detect_task.AsyncResult(task_id)

        if task.state == "PENDING":
            return ApiResponse.success(
                data={"task_id": task_id, "status": "pending", "message": "任务等待中"}
            )
        elif task.state in ["PROGRESS", "STARTED"]:
            return ApiResponse.success(
                data={
                    "task_id": task_id,
                    "status": "processing",
                    "message": "任务处理中",
                }
            )
        elif task.state == "SUCCESS":
            # 从缓存获取结果，直接使用task_id
            cache_key = f"detect:{task_id}"
            result = RedisClient.get_cache(cache_key)
            if result:
                return ApiResponse.success(
                    data={
                        "task_id": task_id,
                        "status": "success",
                        "predictions": result,
                    }
                )
            return ApiResponse.not_found("结果已过期")
        elif task.state == "FAILURE":
            return ApiResponse.internal_error(f"任务失败: {str(task.info)}")
        else:
            logger.warning(f"收到未知任务状态: {task.state}")
            return ApiResponse.success(
                data={
                    "task_id": task_id,
                    "status": "processing",
                    "message": "任务处理中",
                }
            )

    except Exception as e:
        logger.error(f"获取任务结果失败: {str(e)}")
        return ApiResponse.internal_error("获取任务结果失败")


def classify_controller(version: str):
    """
    接收植物图像，进行分类推理

    Args:
        version: 模型版本
    """
    try:
        # 检查请求大小
        if request.content_length and not Config.validate_file_size(
            request.content_length
        ):
            return ApiResponse.file_too_large(
                f"文件大小超过限制（最大{Config.MAX_FILE_SIZE // (1024*1024)}MB）"
            )

        if "image" not in request.files:
            return ApiResponse.bad_request("未提供图片文件")

        # 获取图片文件
        image_file = request.files["image"]
        if not image_file.filename:
            return ApiResponse.bad_request("未选择文件")

        # 检查文件类型
        if not Config.validate_file_extension(image_file.filename):
            return ApiResponse.bad_request("不支持的文件类型，仅支持PNG和JPG格式")

        # 读取图片数据
        image_data = image_file.read()

        # 提交异步任务
        task = classify_task.delay(version, image_data)

        # 返回任务ID
        return ApiResponse.success(
            data={
                "task_id": task.id,
                "status": "processing",
                "message": "任务已提交，请稍后查询结果",
            }
        )

    except RequestEntityTooLarge:
        logger.error("请求文件过大")
        return ApiResponse.file_too_large(
            f"文件大小超过限制（最大{Config.MAX_FILE_SIZE // (1024*1024)}MB）"
        )
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def get_classify_result_controller(task_id: str):
    """获取图像分类任务结果"""
    try:
        # 获取任务状态
        task = classify_task.AsyncResult(task_id)

        if task.state == "PENDING":
            return ApiResponse.success(
                data={"task_id": task_id, "status": "pending", "message": "任务等待中"}
            )
        elif task.state in ["PROGRESS", "STARTED"]:
            return ApiResponse.success(
                data={
                    "task_id": task_id,
                    "status": "processing",
                    "message": "任务处理中",
                }
            )
        elif task.state == "SUCCESS":
            # 从缓存获取结果，直接使用task_id
            cache_key = f"classify:{task_id}"
            result = RedisClient.get_cache(cache_key)
            if result:
                return ApiResponse.success(
                    data={
                        "task_id": task_id,
                        "status": "success",
                        "predictions": result,
                    }
                )
            return ApiResponse.not_found("结果已过期")
        elif task.state == "FAILURE":
            return ApiResponse.internal_error(f"任务失败: {str(task.info)}")
        else:
            logger.warning(f"收到未知任务状态: {task.state}")
            return ApiResponse.success(
                data={
                    "task_id": task_id,
                    "status": "processing",
                    "message": "任务处理中",
                }
            )

    except Exception as e:
        logger.error(f"获取任务结果失败: {str(e)}")
        return ApiResponse.internal_error("获取任务结果失败")


def get_versions_controller():
    """获取所有可用的模型版本"""
    try:
        # 尝试从缓存获取
        cached_versions = RedisClient.get_cache(Config.MODEL_VERSIONS_CACHE_KEY)
        if cached_versions:
            logger.debug("从缓存获取模型版本")
            return ApiResponse.success(data={"versions": cached_versions})

        # 缓存未命中，从数据库获取
        versions = db.get_all_models()

        # 更新缓存
        RedisClient.set_cache(Config.MODEL_VERSIONS_CACHE_KEY, versions)

        return ApiResponse.success(data={"versions": versions})
    except Exception as e:
        logger.error(f"获取模型版本失败: {str(e)}")
        return ApiResponse.internal_error("获取模型版本失败")


def upload_model_controller():
    """
    上传模型文件
    需要在form-data中提供以下参数：
    - version: 模型版本
    - model_type: 模型类型（detect/classify）
    - model: 模型文件
    """
    try:
        # 获取并验证版本
        version = request.form.get("version")
        if not version:
            return ApiResponse.bad_request("未提供模型版本")
        if not isinstance(version, str) or not version.strip():
            return ApiResponse.bad_request("模型版本格式不正确")

        # 获取并验证模型类型
        model_type = request.form.get("model_type")
        if not model_type:
            return ApiResponse.bad_request("未提供模型类型")
        if not Config.validate_model_type(model_type):
            return ApiResponse.bad_request(
                f"不支持的模型类型: {model_type}，仅支持 {Config.MODEL_TYPES}"
            )

        # 检查请求大小
        if request.content_length and not Config.validate_model_size(
            request.content_length
        ):
            return ApiResponse.file_too_large(
                f"模型文件大小超过限制（最大{Config.MODEL_UPLOAD_MAX_SIZE // (1024*1024)}MB）"
            )

        if "model" not in request.files:
            return ApiResponse.bad_request("未提供模型文件")

        # 获取模型文件
        model_file = request.files["model"]
        if not model_file.filename:
            return ApiResponse.bad_request("未选择文件")

        # 检查文件类型
        if not Config.validate_model_extension(model_file.filename):
            return ApiResponse.bad_request(
                f"不支持的文件类型，仅支持 {Config.MODEL_ALLOWED_EXTENSIONS} 格式"
            )

        # 获取保存路径
        save_path = Config.get_model_path(version, model_type)

        # 保存文件
        try:
            model_file.save(save_path)
            logger.info(f"模型文件已保存: {save_path}")
        except Exception as e:
            logger.error(f"保存模型文件失败: {str(e)}")
            return ApiResponse.internal_error("保存模型文件失败")

        # 计算文件哈希
        file_size = save_path.stat().st_size
        with open(save_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # 设置模型参数
        parameters = {
            "conf": 0.25,
            "iou": 0.5 if model_type == "detect" else None,
        }

        # 更新数据库中的模型配置
        if not db.add_model(
            version=version,
            model_type=model_type,
            file_path=str(save_path),
            file_size=file_size,
            file_hash=file_hash,
            parameters=parameters,
        ):
            # 如果数据库更新失败，删除已保存的文件
            if save_path.exists():
                save_path.unlink()
            return ApiResponse.internal_error("保存模型配置失败")

        # 重新加载模型
        try:
            ai_service.model_manager._load_models()
            logger.info(f"模型已重新加载: {version} ({model_type})")
        except Exception as e:
            logger.error(f"重新加载模型失败: {str(e)}")
            # 如果重新加载失败，删除已保存的文件和数据库记录
            if save_path.exists():
                save_path.unlink()
            db.delete_model(version, model_type)
            return ApiResponse.internal_error("模型加载失败")

        return ApiResponse.success(
            message=f"模型上传成功: {version} ({model_type})",
            data={"version": version, "type": model_type, "path": str(save_path)},
        )

    except Exception as e:
        logger.error(f"上传模型时发生错误: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def update_model_controller(model_id: int):
    """
    更新模型配置
    需要在form-data中提供以下参数：
    - conf: 置信度阈值（可选）
    - iou: IoU阈值（可选，仅用于检测模型）
    """
    try:
        # 获取模型信息
        model_data = db.get_model_by_id(model_id)
        if not model_data:
            return ApiResponse.not_found(f"未找到ID为 {model_id} 的模型")

        # 获取并验证参数
        parameters = {}
        conf = request.form.get("conf")
        if conf is not None:
            try:
                conf = float(conf)
                if not 0 <= conf <= 1:
                    return ApiResponse.bad_request("置信度阈值必须在0到1之间")
                parameters["conf"] = conf
            except ValueError:
                return ApiResponse.bad_request("置信度阈值必须是数字")

        iou = request.form.get("iou")
        if iou is not None:
            if model_data["model_type"] != "detect":
                return ApiResponse.bad_request("IoU阈值仅用于检测模型")
            try:
                iou = float(iou)
                if not 0 <= iou <= 1:
                    return ApiResponse.bad_request("IoU阈值必须在0到1之间")
                parameters["iou"] = iou
            except ValueError:
                return ApiResponse.bad_request("IoU阈值必须是数字")

        if not parameters:
            return ApiResponse.bad_request("未提供任何要更新的参数")

        # 更新模型参数
        if not db.update_model_parameters(model_id, parameters):
            return ApiResponse.internal_error("更新模型参数失败")

        # 重新加载模型
        try:
            ai_service.model_manager._load_models()
            # 清除缓存
            RedisClient.delete_cache(Config.MODEL_VERSIONS_CACHE_KEY)
            logger.info(f"模型已重新加载: ID={model_id}")
        except Exception as e:
            logger.error(f"重新加载模型失败: {str(e)}")
            return ApiResponse.internal_error("模型加载失败")

        return ApiResponse.success(
            message=f"模型参数更新成功: ID={model_id}",
            data={"model_id": model_id, "parameters": parameters},
        )

    except Exception as e:
        logger.error(f"更新模型参数时发生错误: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def delete_model_controller(model_id: int):
    """
    删除模型
    """
    try:
        # 获取模型信息
        model_data = db.get_model_by_id(model_id)
        if not model_data:
            return ApiResponse.not_found(f"未找到ID为 {model_id} 的模型")

        # 删除模型文件
        file_path = Path(model_data["file_path"])
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"模型文件已删除: {file_path}")
            except Exception as e:
                logger.error(f"删除模型文件失败: {str(e)}")
                return ApiResponse.internal_error("删除模型文件失败")

        # 删除数据库记录
        if not db.delete_model_by_id(model_id):
            return ApiResponse.internal_error("删除模型记录失败")

        # 重新加载模型
        try:
            ai_service.model_manager._load_models()
            # 清除缓存
            RedisClient.delete_cache(Config.MODEL_VERSIONS_CACHE_KEY)
            logger.info(f"模型已重新加载: ID={model_id}")
        except Exception as e:
            logger.error(f"重新加载模型失败: {str(e)}")
            return ApiResponse.internal_error("模型加载失败")

        return ApiResponse.success(
            message=f"模型删除成功: ID={model_id}",
            data={"model_id": model_id},
        )

    except Exception as e:
        logger.error(f"删除模型时发生错误: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")
