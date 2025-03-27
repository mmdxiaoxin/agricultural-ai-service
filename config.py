import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_env_files():
    """加载环境配置文件"""
    # 首先加载基础配置
    load_dotenv(".env")

    # 获取当前环境
    env = os.getenv("FLASK_ENV", "development")
    env_file = f".env.{env}"

    # 如果存在环境配置文件，则加载它
    if os.path.exists(env_file):
        # 清除之前加载的环境变量
        for key in os.environ.keys():
            if key.startswith(("HOST", "PORT", "FLASK_", "LOG_", "REQUEST_", "JWT_")):
                del os.environ[key]

        # 重新加载基础配置
        load_dotenv(".env")
        # 加载环境特定配置
        load_dotenv(env_file, override=True)
        print(f"已加载环境配置文件: {env_file}")
    else:
        print(f"未找到环境配置文件: {env_file}，使用默认配置")


# 加载环境配置
load_env_files()


class Config:
    """应用配置类"""

    # 基础路径配置
    BASE_DIR = Path(__file__).parent
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

    @classmethod
    def init_app(cls, app):
        """初始化应用配置"""
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
    def get_model_config(cls, version: str) -> Dict[str, Any]:
        """获取指定版本的模型配置"""
        from common.models.database import Database

        db = Database()
        model_data = db.get_model(version, "detect") or db.get_model(
            version, "classify"
        )
        if not model_data:
            raise ValueError(f"未找到模型版本: {version}")
        return model_data

    @classmethod
    def get_all_model_versions(cls) -> Dict[str, list]:
        """获取所有可用的模型版本"""
        from common.models.database import Database

        db = Database()
        return db.get_all_models()

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

        return content_length <= cls.MAX_FILE_SIZE
