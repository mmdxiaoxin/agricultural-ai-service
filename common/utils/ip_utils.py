from functools import wraps
from flask import request
from common.utils.response import ApiResponse
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)


def local_ip_required(f):
    """IP限制装饰器，只允许本地IP访问"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        if client_ip not in ["127.0.0.1", "localhost", "::1"]:
            logger.warning(f"非本地IP访问被拒绝: {client_ip}")
            return ApiResponse.forbidden("只允许本地访问")
        return f(*args, **kwargs)

    return decorated_function
