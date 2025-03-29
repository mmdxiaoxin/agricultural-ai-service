import time
from functools import wraps
from flask import Flask, request
from flask_cors import CORS
from werkzeug.exceptions import RequestTimeout

from config import AppConfig
from modules import modules
from common.utils.response import ApiResponse
from common.utils.redis_utils import RedisClient
from common.utils.error_handler import error_handler
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)

app = Flask(__name__)
cors = CORS(app)


# 请求超时装饰器
def timeout_handler(timeout=AppConfig.REQUEST_TIMEOUT):
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
    if AppConfig.DEBUG:
        logger.debug("Request URL: %s", request.url)
        logger.debug("Request Method: %s", request.method)
        logger.debug("Request Headers: %s", dict(request.headers))


@app.after_request
def log_response_info(response):
    """记录响应信息 - 只在文件日志中记录"""
    if AppConfig.DEBUG:
        logger.debug("Response Status: %s", response.status)
    return response


# 注册所有模块的路由
for module in modules:
    app.register_blueprint(module, url_prefix="/ai")

# 注册错误处理器
error_handler.register_handlers(app)

if __name__ == "__main__":
    try:
        logger.info(f"Starting server on {AppConfig.HOST}:{AppConfig.PORT}")
        app.run(
            debug=AppConfig.DEBUG,
            host=AppConfig.HOST,
            port=AppConfig.PORT,
            threaded=True,
            use_reloader=AppConfig.DEBUG,
        )
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        logger.info("Server is closed")
