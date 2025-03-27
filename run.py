import os
import argparse
from config import AppConfig
from app import app, celery
from config.app_config import load_env_files


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="启动农业AI服务")
    parser.add_argument(
        "--env",
        choices=["development", "production"],
        default="development",
        help="运行环境 (development/production)",
    )
    parser.add_argument(
        "--mode",
        choices=["web", "worker"],
        default="web",
        help="运行模式 (web/worker)",
    )
    parser.add_argument("--port", type=int, help="服务器端口")
    parser.add_argument("--host", help="服务器主机地址")
    parser.add_argument("--debug", action="store_true", help="是否启用调试模式")
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 设置环境变量
    os.environ["FLASK_ENV"] = args.env

    # 加载环境配置
    load_env_files()

    # 初始化配置
    AppConfig.init_app(app)

    if args.mode == "web":
        # 启动Web服务器
        from waitress import serve

        print(
            f"Starting server in {args.env} mode on {AppConfig.HOST}:{AppConfig.PORT}"
        )
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
