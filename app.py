import logging
import os
import time
from logging.handlers import RotatingFileHandler
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import RequestTimeout, RequestEntityTooLarge

from config import Config
from modules import modules

# 加载 .env 文件
load_dotenv()

# 创建日志目录
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(console_formatter)

# 文件处理器
file_handler = RotatingFileHandler(
    os.path.join(log_dir, "app.log"), maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)

# 添加处理器
logger.addHandler(console_handler)
logger.addHandler(file_handler)

app = Flask(__name__)
app.config.from_object(Config)
cors = CORS(app)


# 请求超时装饰器
def timeout_handler(timeout=30):
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
    """记录请求信息"""
    logger.info("Headers: %s", request.headers)
    logger.info("Body: %s", request.get_data())


@app.after_request
def log_response_info(response):
    """记录响应信息"""
    logger.info("Response: %s", response.get_data())
    return response


@app.errorhandler(RequestTimeout)
def handle_timeout(error):
    """处理请求超时错误"""
    logger.error(f"请求超时: {str(error)}")
    return jsonify({"error": "请求处理超时，请稍后重试"}), 408


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    """处理文件过大错误"""
    logger.error(f"文件过大: {str(error)}")
    return jsonify({"error": "文件大小超过限制（最大16MB）"}), 413


@app.errorhandler(Exception)
def handle_generic_error(error):
    """处理通用错误"""
    logger.error(f"未处理的错误: {str(error)}")
    return jsonify({"error": "服务器内部错误"}), 500


# 注册所有模块的路由
for module in modules:
    app.register_blueprint(module, url_prefix="/ai")

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 5000))
    try:
        logger.info(f"Starting server on {host}:{port}")
        app.run(debug=True, host=host, port=port, threaded=True)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        logger.info("Server is closed")
