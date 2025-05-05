from flask import current_app, request
from common.init import initializer
from common.utils.response import ApiResponse, ResponseCode
from common.utils.redis_utils import RedisClient
from common.utils.logger import log_manager
from common.utils.ip_utils import local_ip_required
from config.app_config import Config
from config.resnet_config import ResNetConfig
from config.yolo_config import YOLOConfig
import hashlib
import uuid
import os
import json
from pathlib import Path
from functools import wraps

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


def delete_model_controller(version_id):
    """删除模型版本"""
    try:
        # 获取模型信息
        version = ai_service.model_manager.get_model_by_version_id(version_id)
        if not version:
            return ApiResponse.not_found("模型不存在")

        # 删除模型文件
        file_path = Path(version["file_path"])
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"模型文件已删除: {file_path}")
            except Exception as e:
                logger.error(f"删除模型文件失败: {str(e)}")
                return ApiResponse.internal_error("删除模型文件失败")

        # 删除数据库记录
        if not ai_service.model_manager.delete_version_by_id(version["id"]):
            return ApiResponse.internal_error("删除模型记录失败")

        # 清除缓存
        RedisClient.delete_cache(Config.MODEL_VERSIONS_CACHE_KEY)

        return ApiResponse.success(
            message=f"模型版本删除成功: ID={version['id']}",
            data={"model_id": version["model_id"]},
        )
    except Exception as e:
        logger.error(f"删除模型失败: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def create_upload_task_controller():
    """
    创建分片上传任务
    需要在form-data中提供以下参数：
    - name: 模型名称
    - version: 模型版本
    - model_type: 模型类型（yolo/resnet）
    - model_version: 具体模型版本
    - task_type: 任务类型（detect/classify）
    - total_size: 文件总大小
    - total_chunks: 总分片数
    - description: 模型描述（可选）
    """
    try:
        # 获取并验证必要参数
        name = request.form.get("name", "")
        version = request.form.get("version", "")
        model_type = request.form.get("model_type", "")
        model_version = request.form.get("model_version", "")
        task_type = request.form.get("task_type", "")
        total_size_str = request.form.get("total_size", "")
        total_chunks_str = request.form.get("total_chunks", "")

        if not all(
            [
                name,
                version,
                model_type,
                model_version,
                task_type,
                total_size_str,
                total_chunks_str,
            ]
        ):
            return ApiResponse.bad_request("缺少必要参数")

        # 验证参数
        if model_type not in ["yolo", "resnet"]:
            return ApiResponse.bad_request("不支持的模型类型")
        if task_type not in ["detect", "classify"]:
            return ApiResponse.bad_request("不支持的任务类型")

        try:
            total_size = int(total_size_str)
            total_chunks = int(total_chunks_str)
        except ValueError:
            return ApiResponse.bad_request("文件大小和分片数必须是整数")

        # 生成上传任务ID
        task_id = str(uuid.uuid4())

        # 创建任务信息
        task_info = {
            "name": name,
            "version": version,
            "model_type": model_type,
            "model_version": model_version,
            "task_type": task_type,
            "total_size": total_size,
            "total_chunks": total_chunks,
            "uploaded_chunks": 0,
            "chunks": {},
            "description": request.form.get("description", ""),
            "status": "uploading",
        }

        # 将任务信息存入Redis
        RedisClient.set_cache(
            f"upload_task:{task_id}", json.dumps(task_info), ttl=3600
        )  # 1小时过期

        return ApiResponse.success(
            data={"task_id": task_id, "message": "上传任务创建成功"}
        )

    except Exception as e:
        logger.error(f"创建上传任务失败: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def upload_chunk_controller():
    """
    上传文件分片
    需要在form-data中提供以下参数：
    - task_id: 上传任务ID
    - chunk_index: 分片索引
    - chunk: 分片文件
    """
    try:
        task_id = request.form.get("task_id", "")
        chunk_index_str = request.form.get("chunk_index", "")
        chunk_file = request.files.get("chunk")

        if not all([task_id, chunk_index_str, chunk_file]):
            return ApiResponse.bad_request("缺少必要参数")

        # 获取任务信息
        task_info = RedisClient.get_cache(f"upload_task:{task_id}")
        if not task_info:
            return ApiResponse.not_found("上传任务不存在或已过期")

        # 验证分片索引
        try:
            chunk_index = int(chunk_index_str)
            if chunk_index < 0 or chunk_index >= task_info["total_chunks"]:
                return ApiResponse.bad_request("无效的分片索引")
        except ValueError:
            return ApiResponse.bad_request("分片索引必须是整数")

        # 保存分片
        chunk_dir = Path(Config.UPLOAD_CHUNK_DIR) / task_id
        chunk_dir.mkdir(parents=True, exist_ok=True)

        chunk_path = chunk_dir / f"chunk_{chunk_index}"
        if chunk_file:
            chunk_file.save(str(chunk_path))
        else:
            return ApiResponse.bad_request("分片文件为空")

        # 更新任务信息
        task_info["chunks"][str(chunk_index)] = True
        task_info["uploaded_chunks"] = len(task_info["chunks"])

        RedisClient.set_cache(f"upload_task:{task_id}", json.dumps(task_info), ttl=3600)

        return ApiResponse.success(
            data={
                "task_id": task_id,
                "chunk_index": chunk_index,
                "message": "分片上传成功",
            }
        )

    except Exception as e:
        logger.error(f"上传分片失败: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


@local_ip_required
def merge_chunks_controller():
    """
    合并文件分片
    需要在form-data中提供以下参数：
    - task_id: 上传任务ID
    """
    try:
        task_id = request.form.get("task_id")
        if not task_id:
            return ApiResponse.bad_request("缺少任务ID")

        # 获取任务信息
        task_info = RedisClient.get_cache(f"upload_task:{task_id}")
        if not task_info:
            return ApiResponse.not_found("上传任务不存在或已过期")

        # 检查是否所有分片都已上传
        if task_info["uploaded_chunks"] != task_info["total_chunks"]:
            return ApiResponse.bad_request("还有分片未上传完成")

        # 合并分片
        chunk_dir = Path(Config.UPLOAD_CHUNK_DIR) / task_id
        if not chunk_dir.exists():
            return ApiResponse.not_found("分片目录不存在")

        # 生成最终文件名
        original_extension = "pt"  # PyTorch模型文件扩展名
        filename = f"{uuid.uuid4()}.{original_extension}"
        save_path = Config.get_model_path(filename)

        # 按顺序合并分片
        with open(save_path, "wb") as outfile:
            for i in range(task_info["total_chunks"]):
                chunk_path = chunk_dir / f"chunk_{i}"
                with open(chunk_path, "rb") as infile:
                    outfile.write(infile.read())

        # 计算文件哈希
        with open(save_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # 检查是否已存在相同哈希的模型
        existing_model = ai_service.model_manager.get_model_by_hash(file_hash)
        if existing_model:
            # 删除合并后的文件
            os.remove(save_path)
            return ApiResponse.bad_request(
                f"该模型文件已存在，模型名称: {existing_model['name']}, 版本: {existing_model['version']}"
            )

        # 设置模型参数
        parameters = {}
        if task_info["model_type"] == "yolo":
            parameters = YOLOConfig.get_default_config()
        elif task_info["model_type"] == "resnet":
            parameters = ResNetConfig.get_default_config(task_info["model_version"])

        # 更新数据库中的模型配置
        if not ai_service.model_manager.add_model(
            name=task_info["name"],
            version=task_info["version"],
            task_type=task_info["task_type"],
            file_path=save_path,
            file_size=task_info["total_size"],
            file_hash=file_hash,
            model_version=task_info["model_version"],
            model_type=task_info["model_type"],
            parameters=parameters,
            description=task_info["description"],
        ):
            # 如果数据库更新失败，删除已保存的文件
            if save_path.exists():
                save_path.unlink()
            return ApiResponse.internal_error("保存模型配置失败")

        # 清理分片目录
        for chunk_path in chunk_dir.glob("chunk_*"):
            chunk_path.unlink()
        chunk_dir.rmdir()

        # 清除任务缓存
        RedisClient.delete_cache(f"upload_task:{task_id}")
        RedisClient.delete_cache(Config.MODEL_VERSIONS_CACHE_KEY)

        return ApiResponse.success(
            message=f"模型上传成功: {task_info['name']}-{task_info['version']}-{task_info['task_type']}",
            data={
                "name": task_info["name"],
                "version": task_info["version"],
                "model_type": task_info["model_type"],
                "model_version": task_info["model_version"],
                "task_type": task_info["task_type"],
                "path": str(save_path),
                "file_hash": file_hash,
            },
        )

    except Exception as e:
        logger.error(f"合并分片失败: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")


def upload_model_controller():
    """
    上传模型文件
    需要在form-data中提供以下参数：
    - name: 模型名称（如yolo_v8, resnet50）
    - version: 模型版本
    - model_type: 模型类型（yolo/resnet）
    - model_version: 具体模型版本（如v8, v5, 18, 50等）
    - task_type: 任务类型（detect/classify）
    - model: 模型文件
    - description: 模型描述（可选）
    """
    try:
        # 获取并验证模型名称
        name = request.form.get("name")
        if not name:
            return ApiResponse.bad_request("未提供模型名称")
        if not isinstance(name, str) or not name.strip():
            return ApiResponse.bad_request("模型名称格式不正确")

        # 获取并验证模型类型
        model_type = request.form.get("model_type")
        if not model_type:
            return ApiResponse.bad_request("未提供模型类型")
        if model_type not in ["yolo", "resnet"]:
            return ApiResponse.bad_request("不支持的模型类型，仅支持yolo和resnet")

        # 获取并验证具体模型版本
        model_version = request.form.get("model_version")
        if not model_version:
            return ApiResponse.bad_request("未提供具体模型版本")
        if model_type == "yolo" and model_version not in ["v5", "v8", "v11"]:
            return ApiResponse.bad_request("不支持的YOLO版本，仅支持v5, v8, v11")
        if model_type == "resnet" and model_version not in [
            "18",
            "34",
            "50",
            "101",
            "152",
        ]:
            return ApiResponse.bad_request(
                "不支持的ResNet版本，仅支持18, 34, 50, 101, 152"
            )

        # 获取并验证版本
        version = request.form.get("version")
        if not version:
            return ApiResponse.bad_request("未提供模型版本")
        if not isinstance(version, str) or not version.strip():
            return ApiResponse.bad_request("模型版本格式不正确")

        # 获取并验证任务类型
        task_type = request.form.get("task_type")
        if not task_type:
            return ApiResponse.bad_request("未提供任务类型")
        if task_type not in ["detect", "classify"]:
            return ApiResponse.bad_request("不支持的任务类型，仅支持detect和classify")

        # 检查请求大小
        if request.content_length and not Config.validate_model_size(
            request.content_length
        ):
            return ApiResponse.file_too_large(
                f"模型文件大小超过限制（最大{Config.MODEL_UPLOAD_MAX_SIZE}MB）"
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

        # 计算文件哈希
        file_hash = hashlib.sha256(model_file.read()).hexdigest()
        model_file.seek(0)  # 重置文件指针位置

        # 检查是否已存在相同哈希的模型
        existing_model = ai_service.model_manager.get_model_by_hash(file_hash)
        if existing_model:
            return ApiResponse.bad_request(
                f"该模型文件已存在，模型名称: {existing_model['name']}, 版本: {existing_model['version']}"
            )

        # 生成UUID文件名并保留原始扩展名
        original_extension = model_file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4()}.{original_extension}"
        save_path = Config.get_model_path(filename)

        # 保存文件
        try:
            model_file.save(save_path)
            logger.info(f"模型文件已保存: {save_path}")
        except Exception as e:
            logger.error(f"保存模型文件失败: {str(e)}")
            return ApiResponse.internal_error("保存模型文件失败")

        # 获取文件大小
        file_size = save_path.stat().st_size

        # 设置模型参数
        parameters = {}
        if model_type == "yolo":
            parameters = YOLOConfig.get_default_config()
        elif model_type == "resnet":
            parameters = ResNetConfig.get_default_config(model_version)

        # 获取模型描述
        description = request.form.get("description", "")

        # 更新数据库中的模型配置
        if not ai_service.model_manager.add_model(
            name=name,
            version=version,
            task_type=task_type,
            file_path=save_path,
            file_size=file_size,
            file_hash=file_hash,
            model_version=model_version,
            model_type=model_type,
            parameters=parameters,
            description=description,
        ):
            # 如果数据库更新失败，删除已保存的文件
            if save_path.exists():
                save_path.unlink()
            return ApiResponse.internal_error("保存模型配置失败")

        # 清除缓存
        RedisClient.delete_cache(Config.MODEL_VERSIONS_CACHE_KEY)

        return ApiResponse.success(
            message=f"模型上传成功: {name}-{version}-{task_type}",
            data={
                "name": name,
                "version": version,
                "model_type": model_type,
                "model_version": model_version,
                "task_type": task_type,
                "path": str(save_path),
                "file_hash": file_hash,
            },
        )

    except Exception as e:
        logger.error(f"上传模型时发生错误: {str(e)}")
        return ApiResponse.internal_error(f"服务器内部错误: {str(e)}")
