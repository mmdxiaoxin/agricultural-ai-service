from flask import Blueprint

from .controller import (
    detect_controller,
    classify_controller,
    get_versions_controller,
    upload_model_controller,
)
from common.utils.jwt_utils import require_auth, require_roles

ai_bp = Blueprint("ai", __name__)

# 获取可用模型版本
ai_bp.route("/versions", methods=["GET"])(
    require_auth(require_roles("user", "admin", "expert"))(get_versions_controller)
)

# 检测模型路由
ai_bp.route("/detect/<version>", methods=["POST"])(
    require_auth(require_roles("user", "admin", "expert"))(detect_controller)
)

# 分类模型路由
ai_bp.route("/classify/<version>", methods=["POST"])(
    require_auth(require_roles("user", "admin", "expert"))(classify_controller)
)

# 模型上传路由
ai_bp.route("/upload", methods=["POST"])(
    require_auth(require_roles("admin", "expert"))(upload_model_controller)
)
