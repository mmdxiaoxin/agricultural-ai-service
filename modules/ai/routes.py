from flask import Blueprint

from .controller import (
    detect_controller,
    classify_controller,
    get_versions_controller,
    upload_model_controller,
    update_model_controller,
    delete_model_controller,
)
from common.utils.jwt_utils import apply_auth_decorators

ai_bp = Blueprint("ai", __name__)

# 获取可用模型版本
ai_bp.route("/versions", methods=["GET"])(
    apply_auth_decorators("user", "admin", "expert")(get_versions_controller)
)

# 检测模型路由
ai_bp.route("/detect/<version>", methods=["POST"])(
    apply_auth_decorators("user", "admin", "expert")(detect_controller)
)

# 分类模型路由
ai_bp.route("/classify/<version>", methods=["POST"])(
    apply_auth_decorators("user", "admin", "expert")(classify_controller)
)

# 模型上传路由
ai_bp.route("/upload", methods=["POST"])(
    apply_auth_decorators("admin", "expert")(upload_model_controller)
)

# 模型更新路由
ai_bp.route("/models/<int:model_id>", methods=["PUT"])(
    apply_auth_decorators("admin", "expert")(update_model_controller)
)

# 模型删除路由
ai_bp.route("/models/<int:model_id>", methods=["DELETE"])(
    apply_auth_decorators("admin", "expert")(delete_model_controller)
)
