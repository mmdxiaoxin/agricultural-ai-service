import argparse
import os
from waitress import serve

# 设置环境变量
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
args = parser.parse_args()

os.environ["FLASK_ENV"] = args.env

# 重新加载配置
from config.app_config import load_env_files

load_env_files()

# 导入app
from app import app

print(
    f"Starting server in {args.env} mode on {app.config['HOST']}:{app.config['PORT']}"
)

# Waitress服务器配置
serve(
    app,
    host=app.config["HOST"],
    port=app.config["PORT"],
    threads=16,  # 工作线程数
    connection_limit=2000,  # 连接限制
    channel_timeout=app.config["REQUEST_TIMEOUT"],  # 通道超时
    url_scheme="http",
    ident="Agricultural AI Service",  # 服务器标识
    max_request_body_size=app.config["MAX_FILE_SIZE"],  # 最大请求体大小
    cleanup_interval=30,  # 清理间隔
    log_socket_errors=True,  # 记录socket错误
)
