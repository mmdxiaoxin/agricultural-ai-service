import os
import argparse
import multiprocessing
import psutil
from config import AppConfig
from common.init import initializer
from common.utils.logger import log_manager

logger = log_manager.get_logger(__name__)


def get_server_config():
    """获取服务器配置并计算合适的参数"""
    # 获取CPU核心数
    cpu_count = multiprocessing.cpu_count()

    # 获取可用内存（GB）
    memory = psutil.virtual_memory()
    available_memory_gb = memory.available / (1024**3)

    # 根据CPU核心数计算线程数
    threads = min(cpu_count * 2, 32)  # 每个核心2个线程，最大32个线程

    # 根据内存计算连接限制
    # 假设每个连接占用约1MB内存
    connection_limit = min(int(available_memory_gb * 1024), 2000)

    return {"threads": threads, "connection_limit": connection_limit}


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="启动农业AI服务")
    parser.add_argument(
        "--mode",
        choices=["web", "worker", "all"],
        default="all",
        help="运行模式 (web/worker/all)",
    )
    return parser.parse_args()


def run_web_server(server_config):
    """运行Web服务器"""
    from app import app

    # 初始化配置
    AppConfig.init_app(app)

    logger.info(f"Starting server on {AppConfig.HOST}:{AppConfig.PORT}")
    logger.info(
        f"Server configuration: threads={server_config['threads']}, connection_limit={server_config['connection_limit']}"
    )

    # 根据操作系统选择WSGI服务器
    if os.name == "nt":  # Windows系统
        from waitress import serve

        logger.info("使用Waitress作为WSGI服务器（Windows环境）")
        serve(
            app,
            host=AppConfig.HOST,
            port=AppConfig.PORT,
            threads=server_config["threads"],
            connection_limit=server_config["connection_limit"],
            channel_timeout=AppConfig.REQUEST_TIMEOUT,
            url_scheme="http",
            ident="Agricultural AI Service",
            max_request_body_size=AppConfig.MAX_FILE_SIZE,
            cleanup_interval=30,
            log_socket_errors=True,
        )
    else:  # Linux/Unix系统
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key, value)

            def load(self):
                return self.application

        logger.info("使用Gunicorn作为WSGI服务器（Linux环境）")
        options = {
            "bind": f"{AppConfig.HOST}:{AppConfig.PORT}",
            "workers": server_config["threads"],
            "worker_class": "sync",
            "worker_connections": server_config["connection_limit"],
            "timeout": AppConfig.REQUEST_TIMEOUT,
            "max_request_line": AppConfig.MAX_FILE_SIZE,
            "accesslog": "-",
            "errorlog": "-",
            "loglevel": "info",
        }
        StandaloneApplication(app, options).run()


def run_celery_worker(server_config):
    """运行Celery worker"""
    from app import app
    from celery_app import create_celery_app

    # 初始化配置
    AppConfig.init_app(app)
    # 创建Celery实例
    celery = create_celery_app(app)

    # 根据CPU核心数动态设置并发数
    concurrency = min(server_config["threads"], 8)  # 最大8个worker

    # 根据操作系统选择进程池
    pool = "prefork" if os.name != "nt" else "solo"

    argv = [
        "worker",
        f"--loglevel={AppConfig.LOG_LEVEL}",
        f"--pool={pool}",
        f"--concurrency={concurrency}",
        "--hostname=worker@%h",
        "--queues=detect,classify",
        "--max-tasks-per-child=1000",  # 处理1000个任务后重启worker，防止内存泄漏
        "--max-memory-per-child=1024000",  # 1GB内存限制
        "--prefetch-multiplier=4",  # 每个worker预取4个任务
    ]
    celery.worker_main(argv)


def main():
    """主函数"""
    # 设置多进程启动方法为spawn
    multiprocessing.set_start_method("spawn", force=True)

    # 解析命令行参数
    args = parse_args()

    # 获取服务器配置
    server_config = get_server_config()

    # 初始化所有服务组件
    initializer.init_all()

    if args.mode == "all":
        # 创建进程
        web_process = multiprocessing.Process(
            target=run_web_server, args=(server_config,)
        )
        celery_process = multiprocessing.Process(
            target=run_celery_worker, args=(server_config,)
        )

        try:
            # 启动进程
            web_process.start()
            celery_process.start()

            # 等待进程结束
            web_process.join()
            celery_process.join()
        except KeyboardInterrupt:
            logger.info("正在关闭服务...")
            web_process.terminate()
            celery_process.terminate()
            web_process.join()
            celery_process.join()
        finally:
            logger.info("服务已关闭")
    elif args.mode == "web":
        run_web_server(server_config)
    else:  # worker
        run_celery_worker(server_config)


if __name__ == "__main__":
    main()
