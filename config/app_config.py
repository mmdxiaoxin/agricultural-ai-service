import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_env_files():
    """加载环境配置文件"""

    # 加载基础配置
    load_dotenv(".env")


load_env_files()


class Config:
    """应用配置类"""

    # 基础路径配置
    BASE_DIR = Path(__file__).parent.parent  # 指向项目根目录
    LOG_DIR = BASE_DIR / "logs"
    UPLOAD_DIR = BASE_DIR / "uploads"
    WEIGHT_DIR = BASE_DIR / "weight"
    DATA_DIR = BASE_DIR / "data"  # 数据目录

    # 服务器配置
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # JWT配置
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24小时

    # 请求配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # 30秒

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = LOG_DIR / "app.log"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # 文件上传配置
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

    # 模型配置
    MODEL_TYPES = {"detect", "classify"}
    MODEL_ALLOWED_EXTENSIONS = {"pt", "pth", "onnx"}
    MODEL_UPLOAD_MAX_SIZE = 500 * 1024 * 1024  # 500MB

    # Redis配置
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # 缓存过期时间（秒）

    # 模型版本缓存键
    MODEL_VERSIONS_CACHE_KEY = "ai:model:versions"

    @classmethod
    def init_app(cls, app):
        """初始化应用配置"""
        # 加载环境配置
        load_env_files()

        # 创建必要的目录
        cls._create_directories()

        # 配置Flask应用
        app.config.from_object(cls)

        # 配置CORS
        app.config["CORS_HEADERS"] = "Content-Type"

        # 配置JSON
        app.config["JSON_AS_ASCII"] = False
        app.config["JSONIFY_MIMETYPE"] = "application/json;charset=utf-8"

    @classmethod
    def _create_directories(cls):
        """创建必要的目录"""
        directories = [cls.LOG_DIR, cls.UPLOAD_DIR, cls.WEIGHT_DIR, cls.DATA_DIR]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_model_path(cls, version: str, model_type: str) -> Path:
        """获取模型文件保存路径"""
        model_dir = cls.WEIGHT_DIR / version
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir / f"{model_type}-best.pt"

    @classmethod
    def validate_model_extension(cls, filename: str) -> bool:
        """验证模型文件扩展名"""
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in cls.MODEL_ALLOWED_EXTENSIONS
        )

    @classmethod
    def validate_model_size(cls, content_length: int) -> bool:
        """验证模型文件大小"""
        return content_length <= cls.MODEL_UPLOAD_MAX_SIZE

    @classmethod
    def validate_model_type(cls, model_type: str) -> bool:
        """验证模型类型"""
        return model_type in cls.MODEL_TYPES

    @classmethod
    def validate_file_extension(cls, filename: str) -> bool:
        """验证文件扩展名"""
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in cls.ALLOWED_EXTENSIONS
        )

    @classmethod
    def validate_file_size(cls, content_length: int) -> bool:
        """验证文件大小"""
        return content_length <= cls.MAX_FILE_SIZE
