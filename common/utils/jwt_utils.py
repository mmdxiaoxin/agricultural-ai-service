import jwt
import time
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps
from flask import request, current_app
from common.utils.response import ApiResponse
from config.app_config import Config


class JWTUtils:
    @staticmethod
    def generate_token(user_id: Union[str, int], username: str, roles: list) -> str:
        """
        生成JWT token

        Args:
            user_id: 用户ID（字符串或整数）
            username: 用户名
            roles: 用户角色列表

        Returns:
            str: JWT token
        """
        payload = {
            "userId": str(user_id),
            "username": username,
            "roles": roles,
            "exp": int(time.time()) + Config.JWT_EXPIRE_MINUTES * 60,
        }
        return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT token

        Args:
            token: JWT token

        Returns:
            Optional[Dict[str, Any]]: 解码后的payload，验证失败返回None
        """
        try:
            payload = jwt.decode(
                token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


def require_auth(f: Callable) -> Callable:
    """
    JWT认证装饰器

    Args:
        f: 被装饰的函数

    Returns:
        装饰后的函数
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        # 获取Authorization头
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return ApiResponse.unauthorized("未提供认证信息")

        # 检查Bearer token
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return ApiResponse.unauthorized("认证格式错误")

        # 验证token
        payload = JWTUtils.verify_token(token)
        if not payload:
            return ApiResponse.unauthorized("认证已过期或无效")
        # 将用户信息添加到请求上下文
        setattr(
            current_app,
            "user_info",
            {
                "userId": payload["userId"],
                "username": payload["username"],
                "roles": payload["roles"],
            },
        )

        return f(*args, **kwargs)

    return decorated


def require_roles(*roles: str) -> Callable:
    """
    角色权限装饰器

    Args:
        *roles: 允许的角色列表

    Returns:
        装饰器函数
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            # 检查用户信息是否存在
            if not hasattr(current_app, "user_info"):
                return ApiResponse.unauthorized("未认证")
            # 检查用户角色
            user_roles = getattr(current_app, "user_info", {}).get("roles", [])
            if not any(role in user_roles for role in roles):
                return ApiResponse.forbidden("权限不足")

            return f(*args, **kwargs)

        return decorated

    return decorator


def apply_auth_decorators(*roles: str) -> Callable:
    """
    组合认证和角色装饰器

    Args:
        *roles: 允许的角色列表

    Returns:
        装饰器函数
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            # 检查是否是内部访问
            if request.headers.get("X-Internal-Access") == "true":
                # 检查请求来源IP是否为本地
                if request.remote_addr not in ["127.0.0.1", "localhost"]:
                    return ApiResponse.forbidden("非法访问")
                # 检查请求是否来自管理模块
                if not request.path.startswith("/manage/"):
                    return ApiResponse.forbidden("非法访问")
                # 设置内部访问用户信息
                setattr(
                    current_app,
                    "user_info",
                    {
                        "userId": "system",
                        "username": "system",
                        "roles": ["admin"],
                    },
                )
                return f(*args, **kwargs)

            # 获取Authorization头
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return ApiResponse.unauthorized("未提供认证信息")

            # 检查Bearer token
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return ApiResponse.unauthorized("认证格式错误")

            # 验证token
            payload = JWTUtils.verify_token(token)
            if not payload:
                return ApiResponse.unauthorized("认证已过期或无效")
            # 将用户信息添加到请求上下文
            setattr(
                current_app,
                "user_info",
                {
                    "userId": payload["userId"],
                    "username": payload["username"],
                    "roles": payload["roles"],
                },
            )

            # 检查用户角色
            user_roles = getattr(current_app, "user_info", {}).get("roles", [])
            if not any(role in user_roles for role in roles):
                return ApiResponse.forbidden("权限不足")

            return f(*args, **kwargs)

        return decorated

    return decorator
