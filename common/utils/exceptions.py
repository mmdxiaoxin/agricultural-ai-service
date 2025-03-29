from typing import Any, Dict, Optional
from werkzeug.exceptions import HTTPException
from flask import jsonify

from common.utils.response import ApiResponse
from common.utils.logger import log_manager

logger = log_manager.get_logger(__name__)


class BaseError(HTTPException):
    """基础异常类"""

    def __init__(
        self,
        message: str,
        code: int = 500,
        data: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ):
        super().__init__()
        self.message = message
        self.code = code  # code参数已经有默认值500，所以不会是None
        self.data = data or {}
        self.description = description or message

    def get_response(self):
        """获取错误响应"""
        response, status_code = ApiResponse.error(
            code=self.code, message=self.message, data=self.data  # type: ignore
        )
        return response


class ValidationError(BaseError):
    """验证错误"""

    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=400, data=data)


class AuthenticationError(BaseError):
    """认证错误"""

    def __init__(self, message: str = "未授权访问"):
        super().__init__(message=message, code=401)


class AuthorizationError(BaseError):
    """授权错误"""

    def __init__(self, message: str = "禁止访问"):
        super().__init__(message=message, code=403)


class NotFoundError(BaseError):
    """资源未找到错误"""

    def __init__(self, message: str = "请求的资源不存在"):
        super().__init__(message=message, code=404)


class MethodNotAllowedError(BaseError):
    """方法不允许错误"""

    def __init__(self, message: str = "方法不允许"):
        super().__init__(message=message, code=405)


class ConflictError(BaseError):
    """资源冲突错误"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(message=message, code=409)


class GoneError(BaseError):
    """资源已不存在错误"""

    def __init__(self, message: str = "资源已不存在"):
        super().__init__(message=message, code=410)


class UnsupportedMediaTypeError(BaseError):
    """不支持的媒体类型错误"""

    def __init__(self, message: str = "不支持的媒体类型"):
        super().__init__(message=message, code=415)


class UnprocessableEntityError(BaseError):
    """无法处理的实体错误"""

    def __init__(self, message: str = "无法处理的实体"):
        super().__init__(message=message, code=422)


class FileTooLargeError(BaseError):
    """文件过大错误"""

    def __init__(self, message: str = "文件大小超过限制"):
        super().__init__(message=message, code=413)


class TooManyRequestsError(BaseError):
    """请求过多错误"""

    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(message=message, code=429)


class InternalError(BaseError):
    """服务器内部错误"""

    def __init__(self, message: str = "服务器内部错误"):
        super().__init__(message=message, code=500)


class NotImplementedError(BaseError):
    """未实现错误"""

    def __init__(self, message: str = "未实现"):
        super().__init__(message=message, code=501)


class BadGatewayError(BaseError):
    """网关错误"""

    def __init__(self, message: str = "网关错误"):
        super().__init__(message=message, code=502)


class ServiceUnavailableError(BaseError):
    """服务暂时不可用错误"""

    def __init__(self, message: str = "服务暂时不可用"):
        super().__init__(message=message, code=503)


class GatewayTimeoutError(BaseError):
    """网关超时错误"""

    def __init__(self, message: str = "网关超时"):
        super().__init__(message=message, code=504)


class HTTPVersionNotSupportedError(BaseError):
    """不支持的HTTP版本错误"""

    def __init__(self, message: str = "不支持的HTTP版本"):
        super().__init__(message=message, code=505)


class InsufficientStorageError(BaseError):
    """存储空间不足错误"""

    def __init__(self, message: str = "存储空间不足"):
        super().__init__(message=message, code=507)


class LoopDetectedError(BaseError):
    """检测到循环错误"""

    def __init__(self, message: str = "检测到循环"):
        super().__init__(message=message, code=508)


class BandwidthLimitExceededError(BaseError):
    """超出带宽限制错误"""

    def __init__(self, message: str = "超出带宽限制"):
        super().__init__(message=message, code=509)


class NotExtendedError(BaseError):
    """需要扩展错误"""

    def __init__(self, message: str = "需要扩展"):
        super().__init__(message=message, code=510)


class NetworkAuthenticationRequiredError(BaseError):
    """需要网络认证错误"""

    def __init__(self, message: str = "需要网络认证"):
        super().__init__(message=message, code=511)


class NetworkReadTimeoutError(BaseError):
    """网络读取超时错误"""

    def __init__(self, message: str = "网络读取超时"):
        super().__init__(message=message, code=598)


class NetworkConnectTimeoutError(BaseError):
    """网络连接超时错误"""

    def __init__(self, message: str = "网络连接超时"):
        super().__init__(message=message, code=599)


class ModelError(BaseError):
    """模型相关错误"""

    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=500, data=data)


class DatabaseError(BaseError):
    """数据库相关错误"""

    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=500, data=data)


class RedisError(BaseError):
    """Redis相关错误"""

    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=500, data=data)


class CeleryError(BaseError):
    """Celery相关错误"""

    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=500, data=data)


class ExternalServiceError(BaseError):
    """外部服务错误"""

    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=503, data=data)


class ModelLoadError(ModelError):
    """模型加载失败异常"""

    pass


class ModelInferenceError(ModelError):
    """模型推理失败异常"""

    pass


class ModelSaveError(ModelError):
    """模型保存失败异常"""

    pass


class ModelParamError(ModelError):
    """模型参数错误异常"""

    pass


class ImageProcessError(Exception):
    """图像处理相关的异常"""

    pass
