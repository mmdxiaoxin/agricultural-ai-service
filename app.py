import time
from functools import wraps
from flask import Flask, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import RequestTimeout

from config import AppConfig
from modules.ai import ai_bp
from modules.manage import manage_bp
from modules.health import health_bp
from common.utils.response import ApiResponse
from common.utils.redis_utils import RedisClient
from common.utils.error_handler import error_handler
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)

app = Flask(__name__)

# 配置CORS
cors = CORS(
    app,
    resources={
        r"/*": {
            "origins": AppConfig.CORS_ORIGINS,
            "methods": AppConfig.CORS_METHODS,
            "allow_headers": AppConfig.CORS_ALLOW_HEADERS,
            "supports_credentials": AppConfig.CORS_ALLOW_CREDENTIALS,
        }
    },
)


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


# 注册AI模块
app.register_blueprint(ai_bp, url_prefix="/ai")
# 注册管理模块
app.register_blueprint(manage_bp, url_prefix="/manage")
# 注册健康检查模块
app.register_blueprint(health_bp, url_prefix="/")

# 注册错误处理器
error_handler.register_handlers(app)

if __name__ == "__main__":
    try:
        # 记录启动信息
        logger.info("=" * 50)
        logger.info("服务启动中...")
        logger.info(f"环境: {'开发' if AppConfig.DEBUG else '生产'}")
        logger.info(f"主机: {AppConfig.HOST}")
        logger.info(f"端口: {AppConfig.PORT}")
        logger.info(f"日志级别: {AppConfig.LOG_LEVEL}")
        logger.info(f"请求超时: {AppConfig.REQUEST_TIMEOUT}秒")
        logger.info(f"最大文件大小: {AppConfig.MAX_FILE_SIZE}字节")
        logger.info(f"CORS配置: {AppConfig.CORS_ORIGINS}")
        logger.info("=" * 50)

        app.run(
            debug=AppConfig.DEBUG,
            host=AppConfig.HOST,
            port=AppConfig.PORT,
            threaded=True,
            use_reloader=AppConfig.DEBUG,
        )
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}", exc_info=True)
    finally:
        logger.info("服务已关闭")
