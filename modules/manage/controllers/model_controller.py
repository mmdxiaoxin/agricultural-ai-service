from flask import current_app
from common.init import initializer
from common.utils.response import ApiResponse, ResponseCode
from common.utils.redis_utils import RedisClient
from common.utils.logger import log_manager
from config.app_config import Config
from config.resnet_config import ResNetConfig
from config.yolo_config import YOLOConfig
import hashlib
import uuid
import os
import json
from pathlib import Path

# 获取日志记录器
logger = log_manager.get_logger(__name__)

# 使用ServiceInitializer中的实例
ai_service = initializer.ai_service
db = initializer.model_db


def get_models_controller():
    """获取所有模型"""
    try:
        # 尝试从缓存获取
        cached_models = RedisClient.get_cache(Config.MODEL_VERSIONS_CACHE_KEY)
        if cached_models:
            logger.debug("从缓存获取模型列表")
            return ApiResponse.success(data={"models": cached_models})

        # 缓存未命中，从数据库获取
        models = db.get_all_models()

        # 更新缓存
        RedisClient.set_cache(Config.MODEL_VERSIONS_CACHE_KEY, models)

        return ApiResponse.success(data={"models": models})
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return ApiResponse.internal_error("获取模型列表失败")


def get_model_controller(model_id):
    """获取单个模型详情"""
    try:
        model = db.get_model_by_id(model_id)
        if not model:
            return ApiResponse.not_found("模型不存在")
        return ApiResponse.success(data=model)
    except Exception as e:
        logger.error(f"获取模型详情失败: {str(e)}")
        return ApiResponse.internal_error("获取模型详情失败")


def create_model_controller(data):
    """创建新模型"""
    try:
        # 从data中提取必要参数
        name = data.get("name")
        version = data.get("version")
        task_type = data.get("task_type")
        file_path = data.get("file_path")
        file_size = data.get("file_size")
        file_hash = data.get("file_hash")
        model_version = data.get("model_version")
        model_type = data.get("model_type")
        parameters = data.get("parameters")
        description = data.get("description")

        # 验证必要参数
        if not all(
            [
                name,
                version,
                task_type,
                file_path,
                file_size,
                file_hash,
                model_version,
                model_type,
            ]
        ):
            return ApiResponse.bad_request("缺少必要参数")

        # 检查是否已存在相同哈希的模型
        existing_model = ai_service.model_manager.get_model_by_hash(file_hash)
        if existing_model:
            return ApiResponse.bad_request(
                f"该模型文件已存在，模型名称: {existing_model['name']}, 版本: {existing_model['version']}"
            )

        # 设置模型参数
        if not parameters:
            if model_type == "yolo":
                parameters = YOLOConfig.get_default_config()
            elif model_type == "resnet":
                parameters = ResNetConfig.get_default_config(model_version)

        # 添加模型
        success = ai_service.model_manager.add_model(
            name=name,
            version=version,
            task_type=task_type,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            model_version=model_version,
            model_type=model_type,
            parameters=parameters,
            description=description,
        )

        if not success:
            return ApiResponse.internal_error("创建模型失败")

        # 清除缓存
        RedisClient.delete_cache(Config.MODEL_VERSIONS_CACHE_KEY)

        return ApiResponse.success(
            message=f"模型创建成功: {name}-{version}-{task_type}",
            data={
                "name": name,
                "version": version,
                "model_type": model_type,
                "model_version": model_version,
                "task_type": task_type,
                "path": file_path,
                "file_hash": file_hash,
            },
        )
    except Exception as e:
        logger.error(f"创建模型失败: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def update_model_controller(model_id, data):
    """更新模型"""
    try:
        # 获取模型信息
        model = ai_service.model_manager.get_model_by_id(model_id)
        if not model:
            return ApiResponse.not_found("模型不存在")

        # 更新模型参数
        if "parameters" in data:
            model["parameters"] = data["parameters"]

        # 更新模型描述
        if "description" in data:
            model["description"] = data["description"]

        # 保存更新
        success = ai_service.model_manager.update_model_parameters(
            model_id, model["parameters"]
        )
        if not success:
            return ApiResponse.internal_error("更新失败")

        # 清除缓存
        RedisClient.delete_cache(Config.MODEL_VERSIONS_CACHE_KEY)

        return ApiResponse.success(
            message=f"模型更新成功: ID={model_id}",
            data={"model_id": model_id, "parameters": model["parameters"]},
        )
    except Exception as e:
        logger.error(f"更新模型失败: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def delete_model_controller(model_id):
    """删除模型"""
    try:
        # 获取模型信息
        model = ai_service.model_manager.get_model_by_id(model_id)
        if not model:
            return ApiResponse.not_found("模型不存在")

        # 删除模型文件
        file_path = Path(model["file_path"])
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"模型文件已删除: {file_path}")
            except Exception as e:
                logger.error(f"删除模型文件失败: {str(e)}")
                return ApiResponse.internal_error("删除模型文件失败")

        # 删除数据库记录
        if not ai_service.model_manager.delete_model_by_id(model_id):
            return ApiResponse.internal_error("删除模型记录失败")

        # 清除缓存
        RedisClient.delete_cache(Config.MODEL_VERSIONS_CACHE_KEY)

        return ApiResponse.success(
            message=f"模型删除成功: ID={model_id}",
            data={"model_id": model_id},
        )
    except Exception as e:
        logger.error(f"删除模型失败: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")
