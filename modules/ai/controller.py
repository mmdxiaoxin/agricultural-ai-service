import logging
from flask import request
from werkzeug.exceptions import RequestEntityTooLarge

from common.services.ai_service import AIService
from common.utils.response import ApiResponse, ResponseCode

logger = logging.getLogger(__name__)

# 设置最大请求大小为16MB
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# 创建AI服务实例
ai_service = AIService()


def detect_controller(version: str):
    """
    接收植物图像，进行目标检测推理

    Args:
        version: 模型版本
    """
    try:
        # 检查请求大小
        if request.content_length and request.content_length > MAX_CONTENT_LENGTH:
            return ApiResponse.file_too_large("文件大小超过限制（最大16MB）")

        if "image" not in request.files:
            return ApiResponse.bad_request("未提供图片文件")

        # 获取图片文件
        image_file = request.files["image"]
        if not image_file.filename:
            return ApiResponse.bad_request("未选择文件")

        # 检查文件类型
        if not image_file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
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
        return ApiResponse.file_too_large("文件大小超过限制（最大16MB）")
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
        if request.content_length and request.content_length > MAX_CONTENT_LENGTH:
            return ApiResponse.file_too_large("文件大小超过限制（最大16MB）")

        if "image" not in request.files:
            return ApiResponse.bad_request("未提供图片文件")

        # 获取图片文件
        image_file = request.files["image"]
        if not image_file.filename:
            return ApiResponse.bad_request("未选择文件")

        # 检查文件类型
        if not image_file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
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
        return ApiResponse.file_too_large("文件大小超过限制（最大16MB）")
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def get_versions_controller():
    """获取所有可用的模型版本"""
    try:
        versions = ai_service.get_available_versions()
        return ApiResponse.success(data={"versions": versions})
    except Exception as e:
        logger.error(f"获取模型版本失败: {str(e)}")
        return ApiResponse.internal_error("获取模型版本失败")
