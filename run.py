import argparse
import os
from waitress import serve
from app import app


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="启动农业AI服务")
    parser.add_argument(
        "--env",
        choices=["development", "production"],
        default="development",
        help="运行环境 (development/production)",
    )
    parser.add_argument("--port", type=int, help="服务器端口")
    parser.add_argument("--host", help="服务器主机地址")
    parser.add_argument("--debug", action="store_true", help="是否启用调试模式")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # 设置环境变量
    os.environ["FLASK_ENV"] = args.env

    # 重新加载配置
    from config import load_env_files

    load_env_files()

    print(
        f"Starting server in {args.env} mode on {app.config['HOST']}:{app.config['PORT']}"
    )
    serve(
        app,
        host=app.config["HOST"],
        port=app.config["PORT"],
        threads=4,
        connection_limit=1000,
        channel_timeout=app.config["REQUEST_TIMEOUT"],
        url_scheme="http",
        ident="Agricultural AI Service",
    )
