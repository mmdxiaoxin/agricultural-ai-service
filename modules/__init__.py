from .yolo11 import yolo11_bp
from .yolo5 import yolo5_bp
from .yolo8 import yolo8_bp

# 将所有模块的路由都导入进来，以便在app.py中统一注册
modules = [yolo11_bp, yolo8_bp, yolo5_bp]
