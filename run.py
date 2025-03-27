import os
import argparse
from config import AppConfig
from app import app, celery


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

    if args.mode == "web":
        # 启动Web服务器
        from waitress import serve

        print(f"Starting server on {AppConfig.HOST}:{AppConfig.PORT}")
        serve(
            app,
            host=AppConfig.HOST,
            port=AppConfig.PORT,
            threads=16,
            connection_limit=2000,
            channel_timeout=AppConfig.REQUEST_TIMEOUT,
            url_scheme="http",
            ident="Agricultural AI Service",
            max_request_body_size=AppConfig.MAX_FILE_SIZE,
            cleanup_interval=30,
            log_socket_errors=True,
        )
    else:
        # 启动Celery worker
        argv = [
            "worker",
            "--loglevel=INFO",
            "--pool=solo",  # Windows下使用solo池
            "--concurrency=2",  # 并发worker数
            "--hostname=worker@%h",  # worker主机名
            "--queues=detect,classify",  # 指定要处理的队列
        ]
        celery.worker_main(argv)


if __name__ == "__main__":
    main()
