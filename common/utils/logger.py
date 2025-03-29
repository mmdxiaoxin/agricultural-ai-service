import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import AppConfig


class LogManager:
    """日志管理器，统一管理日志配置"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._setup_logging()

    def _setup_logging(self):
        """配置日志系统"""
        # 确保日志目录存在
        log_dir = Path(AppConfig.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(AppConfig.LOG_LEVEL)

        # 清除现有的处理器
        root_logger.handlers.clear()

        # 控制台处理器 - 只输出错误和警告
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(AppConfig.LOG_FORMAT)
        console_handler.setFormatter(console_formatter)

        # 文件处理器 - 记录所有日志
        file_handler = RotatingFileHandler(
            AppConfig.LOG_FILE,
            maxBytes=AppConfig.LOG_MAX_BYTES,
            backupCount=AppConfig.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(AppConfig.LOG_LEVEL)
        file_formatter = logging.Formatter(AppConfig.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)

        # 添加处理器
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        # 设置第三方库的日志级别
        logging.getLogger("waitress").setLevel(logging.WARNING)
        logging.getLogger("waitress.queue").setLevel(logging.WARNING)
        logging.getLogger("celery").setLevel(logging.WARNING)
        logging.getLogger("celery.task").setLevel(logging.WARNING)
        logging.getLogger("celery.worker").setLevel(logging.WARNING)
        logging.getLogger("celery.app").setLevel(logging.WARNING)
        logging.getLogger("celery.app.trace").setLevel(logging.WARNING)
        logging.getLogger("celery.app.task").setLevel(logging.WARNING)
        logging.getLogger("celery.app.task.trace").setLevel(logging.WARNING)

        logging.info("日志系统初始化完成")

    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        return logging.getLogger(name)


# 创建全局日志管理器实例
log_manager = LogManager()
