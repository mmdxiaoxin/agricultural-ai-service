import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import time
import os

from flask import Flask, request
from flask_cors import CORS
from werkzeug.exceptions import RequestTimeout, RequestEntityTooLarge, HTTPException

from config.app_config import Config
from modules import modules
from common.utils.response import ApiResponse
from common.utils.redis_utils import RedisClient

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(Config.LOG_LEVEL)

# 控制台处理器 - 只输出错误和警告
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # 只显示警告和错误
console_formatter = logging.Formatter(Config.LOG_FORMAT)
console_handler.setFormatter(console_formatter)

# 文件处理器 - 记录所有日志
file_handler = RotatingFileHandler(
    Config.LOG_FILE, maxBytes=Config.LOG_MAX_BYTES, backupCount=Config.LOG_BACKUP_COUNT
)
file_handler.setLevel(Config.LOG_LEVEL)
file_formatter = logging.Formatter(Config.LOG_FORMAT)
file_handler.setFormatter(file_formatter)

# 添加处理器
logger.addHandler(console_handler)
logger.addHandler(file_handler)

app = Flask(__name__)
Config.init_app(app)
cors = CORS(app)


# 请求超时装饰器
def timeout_handler(timeout=Config.REQUEST_TIMEOUT):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            if time.time() - start_time > timeout:
                raise RequestTimeout("请求处理超时")
            return result

        return wrapped

    return decorator


@app.before_request
def log_request_info():
    """记录请求信息 - 只在文件日志中记录"""
    if Config.DEBUG:
        logger.debug("Request URL: %s", request.url)
        logger.debug("Request Method: %s", request.method)
        logger.debug("Request Headers: %s", dict(request.headers))


@app.after_request
def log_response_info(response):
    """记录响应信息 - 只在文件日志中记录"""
    if Config.DEBUG:
        logger.debug("Response Status: %s", response.status)
    return response


@app.errorhandler(RequestTimeout)
def handle_timeout(error):
    """处理请求超时错误"""
    logger.error("Request timeout: %s", str(error))
    return ApiResponse.timeout("请求超时")


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    """处理文件过大错误"""
    logger.error("File too large: %s", str(error))
    return ApiResponse.file_too_large(
        f"文件大小超过限制（最大{Config.MAX_FILE_SIZE // (1024*1024)}MB）"
    )


# 注册所有模块的路由
for module in modules:
    app.register_blueprint(module, url_prefix="/ai")


# 注册错误处理
@app.errorhandler(404)
def not_found_error(error):
    return ApiResponse.not_found("请求的资源不存在")


@app.errorhandler(500)
def internal_error(error):
    return ApiResponse.internal_error("服务器内部错误")


@app.errorhandler(413)
def request_entity_too_large(error):
    return ApiResponse.file_too_large("文件大小超过限制")


@app.errorhandler(400)
def bad_request_error(error):
    return ApiResponse.bad_request(str(error))


@app.errorhandler(401)
def unauthorized_error(error):
    return ApiResponse.unauthorized("未授权访问")


@app.errorhandler(403)
def forbidden_error(error):
    return ApiResponse.forbidden("禁止访问")


@app.errorhandler(429)
def too_many_requests_error(error):
    return ApiResponse.too_many_requests("请求过于频繁")


@app.errorhandler(503)
def service_unavailable_error(error):
    return ApiResponse.service_unavailable("服务暂时不可用")


@app.errorhandler(504)
def gateway_timeout_error(error):
    return ApiResponse.gateway_timeout("网关超时")


@app.errorhandler(505)
def http_version_not_supported_error(error):
    return ApiResponse.http_version_not_supported("不支持的HTTP版本")


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    """处理HTTP异常"""
    error_code = error.code
    error_message = str(error)

    # 根据错误码返回不同的响应
    if error_code == 507:
        return ApiResponse.insufficient_storage("存储空间不足")
    elif error_code == 508:
        return ApiResponse.loop_detected("检测到循环")
    elif error_code == 509:
        return ApiResponse.bandwidth_limit_exceeded("超出带宽限制")
    elif error_code == 510:
        return ApiResponse.not_extended("需要扩展")
    elif error_code == 511:
        return ApiResponse.network_authentication_required("需要网络认证")
    elif error_code == 598:
        return ApiResponse.network_read_timeout("网络读取超时")
    elif error_code == 599:
        return ApiResponse.network_connect_timeout("网络连接超时")
    else:
        return ApiResponse.internal_error(error_message)


@app.errorhandler(Exception)
def handle_exception(error):
    """处理通用错误"""
    logger.error("Unhandled error: %s", str(error))
    return ApiResponse.internal_error("服务器内部错误")


# 注册请求前处理
@app.before_request
def before_request():
    # 这里可以添加请求前的处理逻辑
    pass


# 注册请求后处理
@app.after_request
def after_request(response):
    # 这里可以添加请求后的处理逻辑
    return response


# 注册关闭处理
@app.teardown_appcontext
def teardown_appcontext(error):
    # 这里可以添加应用上下文关闭时的清理逻辑
    pass


if __name__ == "__main__":
    try:
        logger.info(f"Starting server on {Config.HOST}:{Config.PORT}")
        app.run(
            debug=Config.DEBUG,
            host=Config.HOST,
            port=Config.PORT,
            threaded=True,
            use_reloader=Config.DEBUG,
        )
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        logger.info("Server is closed")
