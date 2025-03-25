from flask import Blueprint

from .controller import detect_controller, classify_controller, get_versions_controller

ai_bp = Blueprint("ai", __name__)

# 获取可用模型版本
ai_bp.route("/versions", methods=["GET"])(get_versions_controller)

# 检测模型路由
ai_bp.route("/detect/<version>", methods=["POST"])(detect_controller)

# 分类模型路由
ai_bp.route("/classify/<version>", methods=["POST"])(classify_controller)
