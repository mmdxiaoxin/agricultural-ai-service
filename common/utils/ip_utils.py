from functools import wraps
from flask import request
from common.utils.response import ApiResponse
from common.utils.logger import log_manager
from config.app_config import Config

# 获取日志记录器
logger = log_manager.get_logger(__name__)


def local_ip_required(f):
    """IP限制装饰器，只允许配置的IP访问"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        if client_ip not in Config.ALLOWED_IPS:
            logger.warning(f"非允许IP访问被拒绝: {client_ip}")
            return ApiResponse.forbidden("IP访问受限")
        return f(*args, **kwargs)

    return decorated_function
