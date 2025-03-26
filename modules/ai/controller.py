import logging
import shutil
from flask import request
from werkzeug.exceptions import RequestEntityTooLarge
from pathlib import Path
import hashlib

from services.ai_service import AIService
from common.utils.response import ApiResponse, ResponseCode
from config import Config
from common.models.database import Database

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

        # 调用服务层进行推理
        image_data = image_file.read()
        result = ai_service.detect(version, image_data)

        if result is None:
            return ApiResponse.not_found(f"未找到模型版本: {version}")

        # 返回推理结果
        return ApiResponse.success(data={"predictions": result})

    except RequestEntityTooLarge:
        logger.error("请求文件过大")
        return ApiResponse.file_too_large(
            f"文件大小超过限制（最大{Config.MAX_FILE_SIZE // (1024*1024)}MB）"
        )
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


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

        # 调用服务层进行推理
        image_data = image_file.read()
        result = ai_service.classify(version, image_data)

        if result is None:
            return ApiResponse.not_found(f"未找到模型版本: {version}")

        # 返回推理结果
        return ApiResponse.success(data={"predictions": result})

    except RequestEntityTooLarge:
        logger.error("请求文件过大")
        return ApiResponse.file_too_large(
            f"文件大小超过限制（最大{Config.MAX_FILE_SIZE // (1024*1024)}MB）"
        )
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def get_versions_controller():
    """获取所有可用的模型版本"""
    try:
        versions = db.get_all_models()
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
