import logging
import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from config import Config
from modules import modules

# 加载 .env 文件
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object(Config)
cors = CORS(app)

# 注册所有模块的路由
for module in modules:
    app.register_blueprint(module)

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")  # 从环境变量中获取HOST
    port = int(os.getenv("PORT", 5000))  # 从环境变量中获取PORT
    app.run(debug=True, host=host, port=port)
    print("the server is closed")
