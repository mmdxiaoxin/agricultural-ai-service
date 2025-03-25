import os


class Config:
    # 基础配置
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # 请求配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    SEND_FILE_MAX_AGE_DEFAULT = 0

    # 超时设置
    PERMANENT_SESSION_LIFETIME = 1800  # 30分钟
    SEND_FILE_MAX_AGE_DEFAULT = 0

    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "logs", "app.log"
    )

    # 跨域配置
    CORS_HEADERS = "Content-Type"

    # 性能配置
    JSON_AS_ASCII = False
    JSONIFY_MIMETYPE = "application/json;charset=utf-8"

    @staticmethod
    def init_app(app):
        # 确保上传目录存在
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
