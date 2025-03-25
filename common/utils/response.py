from typing import Any, Dict, Optional, Union
from flask import jsonify


class ResponseCode:
    """响应状态码"""

    SUCCESS = 200
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    REQUEST_TIMEOUT = 408
    FILE_TOO_LARGE = 413
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class ApiResponse:
    """API响应封装类"""

    @staticmethod
    def success(data: Any = None, message: str = "success") -> tuple:
        """
        成功响应

        Args:
            data: 响应数据
            message: 响应消息

        Returns:
            tuple: (response, status_code)
        """
        return (
            jsonify({"code": ResponseCode.SUCCESS, "message": message, "data": data}),
            ResponseCode.SUCCESS,
        )

    @staticmethod
    def error(code: int, message: str, data: Any = None) -> tuple:
        """
        错误响应

        Args:
            code: 错误码
            message: 错误信息
            data: 错误详情

        Returns:
            tuple: (response, status_code)
        """
        return jsonify({"code": code, "message": message, "data": data}), code

    @staticmethod
    def bad_request(message: str = "请求参数错误", data: Any = None) -> tuple:
        """400错误响应"""
        return ApiResponse.error(ResponseCode.BAD_REQUEST, message, data)

    @staticmethod
    def unauthorized(message: str = "未授权访问", data: Any = None) -> tuple:
        """401错误响应"""
        return ApiResponse.error(ResponseCode.UNAUTHORIZED, message, data)

    @staticmethod
    def forbidden(message: str = "禁止访问", data: Any = None) -> tuple:
        """403错误响应"""
        return ApiResponse.error(ResponseCode.FORBIDDEN, message, data)

    @staticmethod
    def not_found(message: str = "资源不存在", data: Any = None) -> tuple:
        """404错误响应"""
        return ApiResponse.error(ResponseCode.NOT_FOUND, message, data)

    @staticmethod
    def timeout(message: str = "请求超时", data: Any = None) -> tuple:
        """408错误响应"""
        return ApiResponse.error(ResponseCode.REQUEST_TIMEOUT, message, data)

    @staticmethod
    def file_too_large(message: str = "文件大小超过限制", data: Any = None) -> tuple:
        """413错误响应"""
        return ApiResponse.error(ResponseCode.FILE_TOO_LARGE, message, data)

    @staticmethod
    def internal_error(message: str = "服务器内部错误", data: Any = None) -> tuple:
        """500错误响应"""
        return ApiResponse.error(ResponseCode.INTERNAL_ERROR, message, data)

    @staticmethod
    def service_unavailable(message: str = "服务暂时不可用", data: Any = None) -> tuple:
        """503错误响应"""
        return ApiResponse.error(ResponseCode.SERVICE_UNAVAILABLE, message, data)
