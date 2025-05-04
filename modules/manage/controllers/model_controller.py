from flask import current_app
from common.init import initializer
from common.utils.response import ApiResponse, ResponseCode


def get_models():
    """获取所有模型"""
    try:
        models = initializer.model_db.get_all_models()
        return ApiResponse.success(data=models)
    except Exception as e:
        return ApiResponse.internal_error(str(e))


def get_model(model_id):
    """获取单个模型详情"""
    try:
        model = initializer.model_db.get_model_by_id(model_id)
        if not model:
            return ApiResponse.not_found("模型不存在")
        return ApiResponse.success(data=model)
    except Exception as e:
        return ApiResponse.internal_error(str(e))


def create_model(data):
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

        # 添加模型
        success = initializer.model_db.add_model(
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
        return ApiResponse.success(message="创建成功")
    except Exception as e:
        return ApiResponse.internal_error(str(e))


def update_model(model_id, data):
    """更新模型"""
    try:
        # 获取模型信息
        model = initializer.model_db.get_model_by_id(model_id)
        if not model:
            return ApiResponse.not_found("模型不存在")

        # 更新模型参数
        if "parameters" in data:
            model["parameters"] = data["parameters"]

        # 更新模型描述
        if "description" in data:
            model["description"] = data["description"]

        # 保存更新
        success = initializer.model_db.add_model(
            name=model["name"],
            version=model["version"],
            task_type=model["task_types"][0],  # 使用第一个任务类型
            file_path=model["file_path"],
            file_size=model["file_size"],
            file_hash=model["file_hash"],
            model_version=model["model_version"],
            model_type=model["model_type"],
            parameters=model["parameters"],
            description=model["description"],
        )

        if not success:
            return ApiResponse.internal_error("更新失败")
        return ApiResponse.success(message="更新成功")
    except Exception as e:
        return ApiResponse.internal_error(str(e))


def delete_model(model_id):
    """删除模型"""
    try:
        # 获取模型信息
        model = initializer.model_db.get_model_by_id(model_id)
        if not model:
            return ApiResponse.not_found("模型不存在")

        # 删除模型文件
        import os

        if os.path.exists(model["file_path"]):
            os.remove(model["file_path"])

        # 删除数据库记录
        success = initializer.model_db.add_model(
            name=model["name"],
            version=model["version"],
            task_type=model["task_types"][0],  # 使用第一个任务类型
            file_path="",  # 空路径表示删除
            file_size=0,
            file_hash="",
            model_version=model["model_version"],
            model_type=model["model_type"],
            parameters=None,
            description=None,
        )

        if not success:
            return ApiResponse.internal_error("删除失败")
        return ApiResponse.success(message="删除成功")
    except Exception as e:
        return ApiResponse.internal_error(str(e))
