# modules/__init__.py
from .task import task_bp

# 将所有模块的路由都导入进来，以便在app.py中统一注册
modules = [task_bp]
