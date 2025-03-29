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


class FileTooLargeError(BaseError):
    """文件过大错误"""

    def __init__(self, message: str = "文件大小超过限制"):
        super().__init__(message=message, code=413)


class TooManyRequestsError(BaseError):
    """请求过多错误"""

    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(message=message, code=429)


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
