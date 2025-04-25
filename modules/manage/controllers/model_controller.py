import requests
from flask import current_app
from common.utils.response import ApiResponse


def get_models():
    """获取所有模型"""
    try:
        response = requests.get(f"{current_app.config['API_BASE_URL']}/ai/versions")
        if response.status_code == 200:
            return ApiResponse.success(data=response.json()["data"])
        return ApiResponse.error(response.status_code, response.json()["message"])
    except Exception as e:
        return ApiResponse.internal_error(str(e))


def get_model(model_id):
    """获取单个模型详情"""
    try:
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/ai/models/{model_id}"
        )
        if response.status_code == 200:
            return ApiResponse.success(data=response.json()["data"])
        return ApiResponse.error(response.status_code, response.json()["message"])
    except Exception as e:
        return ApiResponse.internal_error(str(e))


def create_model(data):
    """创建新模型"""
    try:
        response = requests.post(
            f"{current_app.config['API_BASE_URL']}/ai/upload", json=data
        )
        if response.status_code == 200:
            return ApiResponse.success(data=response.json()["data"])
        return ApiResponse.error(response.status_code, response.json()["message"])
    except Exception as e:
        return ApiResponse.internal_error(str(e))


def update_model(model_id, data):
    """更新模型"""
    try:
        response = requests.put(
            f"{current_app.config['API_BASE_URL']}/ai/models/{model_id}", json=data
        )
        if response.status_code == 200:
            return ApiResponse.success(data=response.json()["data"])
        return ApiResponse.error(response.status_code, response.json()["message"])
    except Exception as e:
        return ApiResponse.internal_error(str(e))


def delete_model(model_id):
    """删除模型"""
    try:
        response = requests.delete(
            f"{current_app.config['API_BASE_URL']}/ai/models/{model_id}"
        )
        if response.status_code == 200:
            return ApiResponse.success()
        return ApiResponse.error(response.status_code, response.json()["message"])
    except Exception as e:
        return ApiResponse.internal_error(str(e))
