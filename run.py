import os
import argparse
import multiprocessing
import psutil
from config import AppConfig
from app import app, celery
from common.init import initializer


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
        choices=["web", "worker"],
        default="web",
        help="运行模式 (web/worker)",
    )
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 初始化配置
    AppConfig.init_app(app)

    # 初始化所有服务组件
    initializer.init_all()

    if args.mode == "web":
        # 获取服务器配置
        server_config = get_server_config()

        # 启动Web服务器
        from waitress import serve

        print(f"Starting server on {AppConfig.HOST}:{AppConfig.PORT}")
        print(
            f"Server configuration: threads={server_config['threads']}, connection_limit={server_config['connection_limit']}"
        )

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
    else:
        # 获取服务器配置
        server_config = get_server_config()

        # 启动Celery worker
        # 根据CPU核心数设置并发worker数
        concurrency = min(server_config["threads"], 4)  # 最大4个worker

        argv = [
            "worker",
            "--loglevel=INFO",  # 只输出INFO级别日志 # WARNING则只输出警告和错误
            "--pool=solo",  # Windows下使用solo池
            f"--concurrency={concurrency}",  # 动态设置并发worker数
            "--hostname=worker@%h",  # worker主机名
            "--queues=detect,classify",  # 指定要处理的队列
        ]
        celery.worker_main(argv)


if __name__ == "__main__":
    main()
