import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import time
import os

from flask import Flask, request
from flask_cors import CORS
from werkzeug.exceptions import RequestTimeout, RequestEntityTooLarge

from config import Config
from modules import modules
from common.utils.response import ApiResponse

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

# 设置环境变量
os.environ["FLASK_ENV"] = "production" if not Config.DEBUG else "development"


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
    logger.debug("Request URL: %s", request.url)
    logger.debug("Request Method: %s", request.method)
    logger.debug("Request Headers: %s", dict(request.headers))


@app.after_request
def log_response_info(response):
    """记录响应信息 - 只在文件日志中记录"""
    logger.debug("Response Status: %s", response.status)
    return response


@app.errorhandler(RequestTimeout)
def handle_timeout(error):
    """处理请求超时错误"""
    logger.error("Request timeout: %s", str(error))
    return ApiResponse.timeout("请求处理超时，请稍后重试")


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    """处理文件过大错误"""
    logger.error("File too large: %s", str(error))
    return ApiResponse.file_too_large(
        f"文件大小超过限制（最大{Config.MAX_FILE_SIZE // (1024*1024)}MB）"
    )


@app.errorhandler(Exception)
def handle_generic_error(error):
    """处理通用错误"""
    logger.error("Unhandled error: %s", str(error))
    return ApiResponse.internal_error("服务器内部错误")


# 注册所有模块的路由
for module in modules:
    app.register_blueprint(module, url_prefix="/ai")

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
