import logging
from typing import Callable, Dict, Type, Union
from werkzeug.exceptions import HTTPException, RequestTimeout, RequestEntityTooLarge

from flask import Flask
from common.utils.response import ApiResponse
from common.utils.logger import log_manager
from common.utils.exceptions import (
    BaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    MethodNotAllowedError,
    ConflictError,
    GoneError,
    UnsupportedMediaTypeError,
    UnprocessableEntityError,
    FileTooLargeError,
    TooManyRequestsError,
    InternalError,
    NotImplementedError,
    BadGatewayError,
    ServiceUnavailableError,
    GatewayTimeoutError,
    HTTPVersionNotSupportedError,
    InsufficientStorageError,
    LoopDetectedError,
    BandwidthLimitExceededError,
    NotExtendedError,
    NetworkAuthenticationRequiredError,
    NetworkReadTimeoutError,
    NetworkConnectTimeoutError,
)
from config import AppConfig

logger = log_manager.get_logger(__name__)


class ErrorHandler:
    """错误处理器，统一管理错误处理"""

    _instance = None
    _error_handlers: Dict[Union[int, Type[Exception]], Callable] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._setup_error_handlers()

    def _setup_error_handlers(self):
        """配置错误处理器"""
        # 配置HTTP错误处理器
        http_handlers: Dict[Type[BaseError], Callable] = {
            ValidationError: lambda e: ApiResponse.bad_request(str(e)),
            AuthenticationError: lambda e: ApiResponse.unauthorized("未授权访问"),
            AuthorizationError: lambda e: ApiResponse.forbidden("禁止访问"),
            NotFoundError: lambda e: ApiResponse.not_found("请求的资源不存在"),
            MethodNotAllowedError: lambda e: ApiResponse.method_not_allowed(
                "方法不允许"
            ),
            ConflictError: lambda e: ApiResponse.conflict("资源冲突"),
            GoneError: lambda e: ApiResponse.gone("资源已不存在"),
            UnsupportedMediaTypeError: lambda e: ApiResponse.unsupported_media_type(
                "不支持的媒体类型"
            ),
            UnprocessableEntityError: lambda e: ApiResponse.unprocessable_entity(
                "无法处理的实体"
            ),
            FileTooLargeError: lambda e: ApiResponse.file_too_large("文件大小超过限制"),
            TooManyRequestsError: lambda e: ApiResponse.too_many_requests(
                "请求过于频繁"
            ),
            InternalError: lambda e: ApiResponse.internal_error("服务器内部错误"),
            NotImplementedError: lambda e: ApiResponse.not_implemented("未实现"),
            BadGatewayError: lambda e: ApiResponse.bad_gateway("网关错误"),
            ServiceUnavailableError: lambda e: ApiResponse.service_unavailable(
                "服务暂时不可用"
            ),
            GatewayTimeoutError: lambda e: ApiResponse.gateway_timeout("网关超时"),
            HTTPVersionNotSupportedError: lambda e: ApiResponse.http_version_not_supported(
                "不支持的HTTP版本"
            ),
            InsufficientStorageError: lambda e: ApiResponse.insufficient_storage(
                "存储空间不足"
            ),
            LoopDetectedError: lambda e: ApiResponse.loop_detected("检测到循环"),
            BandwidthLimitExceededError: lambda e: ApiResponse.bandwidth_limit_exceeded(
                "超出带宽限制"
            ),
            NotExtendedError: lambda e: ApiResponse.not_extended("需要扩展"),
            NetworkAuthenticationRequiredError: lambda e: ApiResponse.network_authentication_required(
                "需要网络认证"
            ),
            NetworkReadTimeoutError: lambda e: ApiResponse.network_read_timeout(
                "网络读取超时"
            ),
            NetworkConnectTimeoutError: lambda e: ApiResponse.network_connect_timeout(
                "网络连接超时"
            ),
        }

        # 配置特殊错误处理器
        exception_handlers: Dict[Type[Exception], Callable] = {
            RequestTimeout: lambda e: ApiResponse.timeout("请求超时"),
            RequestEntityTooLarge: lambda e: ApiResponse.file_too_large(
                f"文件大小超过限制（最大{AppConfig.MAX_FILE_SIZE // (1024*1024)}MB）"
            ),
        }

        # 合并所有处理器
        for exc_type, handler in http_handlers.items():
            self._error_handlers[exc_type] = handler
        for exc_type, handler in exception_handlers.items():
            self._error_handlers[exc_type] = handler

    def register_handlers(self, app: Flask):
        """注册错误处理器到Flask应用"""
        try:
            # 注册错误处理器
            for exc_type, handler in self._error_handlers.items():
                app.register_error_handler(exc_type, handler)

            # 注册通用错误处理器
            @app.errorhandler(Exception)
            def handle_exception(error):
                """处理通用错误"""
                logger.error("Unhandled error: %s", str(error))
                return ApiResponse.internal_error("服务器内部错误")

            logger.info("错误处理器注册完成")
        except Exception as e:
            logger.error(f"错误处理器注册失败: {str(e)}")
            raise


# 创建全局错误处理器实例
error_handler = ErrorHandler()
