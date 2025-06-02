import os
import multiprocessing

# 设置多进程启动方法
if os.name != "nt":  # 如果不是Windows系统（即Linux/Unix系统）
    import torch.multiprocessing as torch_mp

    torch_mp.set_start_method("spawn", force=True)
    multiprocessing.set_start_method("spawn", force=True)

import argparse
import psutil
from config import AppConfig
from config.env_config import EnvConfig
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

    # 获取线程数配置
    threads = EnvConfig.get_server_threads(cpu_count)
    logger.info(f"服务器线程数: {threads} (CPU核心数: {cpu_count})")

    # 根据内存计算连接限制
    # 假设每个连接占用约1MB内存
    connection_limit = min(int(available_memory_gb * 1024), 2000)

    # 检查是否在Docker环境中运行
    is_docker = os.path.exists("/.dockerenv")

    return {
        "threads": threads,
        "connection_limit": connection_limit,
        "is_docker": is_docker,
    }


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

    host = AppConfig.HOST

    logger.info(f"Starting server on {host}:{AppConfig.PORT}")
    logger.info(
        f"Server configuration: threads={server_config['threads']}, connection_limit={server_config['connection_limit']}"
    )

    # 根据操作系统选择WSGI服务器
    if os.name == "nt":  # Windows系统
        from waitress import serve

        logger.info("使用Waitress作为WSGI服务器（Windows环境）")
        serve(
            app,
            host=host,
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
            "bind": f"{host}:{AppConfig.PORT}",
            "workers": server_config["threads"],
            "worker_class": "sync",
            "timeout": AppConfig.REQUEST_TIMEOUT,
            "accesslog": "-",
            "errorlog": "-",
            "loglevel": "info",
            "keepalive": 30,
            "worker_connections": server_config["connection_limit"],
            "forwarded_allow_ips": "*",  # 允许所有代理IP
            "proxy_protocol": False,  # 禁用代理协议
            "proxy_allow_ips": "*",  # 允许所有代理IP
        }

        # 直接运行Gunicorn
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
    celery.conf.worker_concurrency = concurrency

    # 启动worker
    argv = [
        "worker",
        f"--loglevel={AppConfig.LOG_LEVEL}",
        "--hostname=worker@%h",
    ]
    celery.worker_main(argv=argv)


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 获取服务器配置
    server_config = get_server_config()

    # 初始化所有服务组件
    initializer.init_all()

    if args.mode == "all":
        # 创建进程
        web_process = multiprocessing.Process(
            target=run_web_server, args=(server_config,), daemon=True
        )
        celery_process = multiprocessing.Process(
            target=run_celery_worker, args=(server_config,), daemon=True
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
