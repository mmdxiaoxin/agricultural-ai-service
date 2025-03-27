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
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    GONE = 410
    UNSUPPORTED_MEDIA_TYPE = 415
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    INSUFFICIENT_STORAGE = 507
    LOOP_DETECTED = 508
    BANDWIDTH_LIMIT_EXCEEDED = 509
    NOT_EXTENDED = 510
    NETWORK_AUTHENTICATION_REQUIRED = 511
    NETWORK_READ_TIMEOUT = 598
    NETWORK_CONNECT_TIMEOUT = 599
    TIMEOUT = 408


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
    def error(code: int, message: str = "error", data: Any = None) -> tuple:
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
    def method_not_allowed(message: str = "方法不允许", data: Any = None) -> tuple:
        """405错误响应"""
        return ApiResponse.error(ResponseCode.METHOD_NOT_ALLOWED, message, data)

    @staticmethod
    def conflict(message: str = "资源冲突", data: Any = None) -> tuple:
        """409错误响应"""
        return ApiResponse.error(ResponseCode.CONFLICT, message, data)

    @staticmethod
    def gone(message: str = "资源已不存在", data: Any = None) -> tuple:
        """410错误响应"""
        return ApiResponse.error(ResponseCode.GONE, message, data)

    @staticmethod
    def unsupported_media_type(
        message: str = "不支持的媒体类型", data: Any = None
    ) -> tuple:
        """415错误响应"""
        return ApiResponse.error(ResponseCode.UNSUPPORTED_MEDIA_TYPE, message, data)

    @staticmethod
    def unprocessable_entity(
        message: str = "无法处理的实体", data: Any = None
    ) -> tuple:
        """422错误响应"""
        return ApiResponse.error(ResponseCode.UNPROCESSABLE_ENTITY, message, data)

    @staticmethod
    def too_many_requests(message: str = "请求过于频繁", data: Any = None) -> tuple:
        """429错误响应"""
        return ApiResponse.error(ResponseCode.TOO_MANY_REQUESTS, message, data)

    @staticmethod
    def internal_error(message: str = "服务器内部错误", data: Any = None) -> tuple:
        """500错误响应"""
        return ApiResponse.error(ResponseCode.INTERNAL_ERROR, message, data)

    @staticmethod
    def not_implemented(message: str = "未实现", data: Any = None) -> tuple:
        """501错误响应"""
        return ApiResponse.error(ResponseCode.NOT_IMPLEMENTED, message, data)

    @staticmethod
    def bad_gateway(message: str = "网关错误", data: Any = None) -> tuple:
        """502错误响应"""
        return ApiResponse.error(ResponseCode.BAD_GATEWAY, message, data)

    @staticmethod
    def service_unavailable(message: str = "服务暂时不可用", data: Any = None) -> tuple:
        """503错误响应"""
        return ApiResponse.error(ResponseCode.SERVICE_UNAVAILABLE, message, data)

    @staticmethod
    def gateway_timeout(message: str = "网关超时", data: Any = None) -> tuple:
        """504错误响应"""
        return ApiResponse.error(ResponseCode.GATEWAY_TIMEOUT, message, data)

    @staticmethod
    def http_version_not_supported(
        message: str = "不支持的HTTP版本", data: Any = None
    ) -> tuple:
        """505错误响应"""
        return ApiResponse.error(ResponseCode.HTTP_VERSION_NOT_SUPPORTED, message, data)

    @staticmethod
    def insufficient_storage(message: str = "存储空间不足", data: Any = None) -> tuple:
        """507错误响应"""
        return ApiResponse.error(ResponseCode.INSUFFICIENT_STORAGE, message, data)

    @staticmethod
    def loop_detected(message: str = "检测到循环", data: Any = None) -> tuple:
        """508错误响应"""
        return ApiResponse.error(ResponseCode.LOOP_DETECTED, message, data)

    @staticmethod
    def bandwidth_limit_exceeded(
        message: str = "超出带宽限制", data: Any = None
    ) -> tuple:
        """509错误响应"""
        return ApiResponse.error(ResponseCode.BANDWIDTH_LIMIT_EXCEEDED, message, data)

    @staticmethod
    def not_extended(message: str = "需要扩展", data: Any = None) -> tuple:
        """510错误响应"""
        return ApiResponse.error(ResponseCode.NOT_EXTENDED, message, data)

    @staticmethod
    def network_authentication_required(
        message: str = "需要网络认证", data: Any = None
    ) -> tuple:
        """511错误响应"""
        return ApiResponse.error(
            ResponseCode.NETWORK_AUTHENTICATION_REQUIRED, message, data
        )

    @staticmethod
    def network_read_timeout(message: str = "网络读取超时", data: Any = None) -> tuple:
        """598错误响应"""
        return ApiResponse.error(ResponseCode.NETWORK_READ_TIMEOUT, message, data)

    @staticmethod
    def network_connect_timeout(
        message: str = "网络连接超时", data: Any = None
    ) -> tuple:
        """599错误响应"""
        return ApiResponse.error(ResponseCode.NETWORK_CONNECT_TIMEOUT, message, data)

    @staticmethod
    def file_too_large(message: str = "文件大小超过限制", data: Any = None) -> tuple:
        """413错误响应"""
        return ApiResponse.error(ResponseCode.FILE_TOO_LARGE, message, data)

    @staticmethod
    def timeout(message: str = "请求超时", data: Any = None) -> tuple:
        """408错误响应"""
        return ApiResponse.error(ResponseCode.TIMEOUT, message, data)
