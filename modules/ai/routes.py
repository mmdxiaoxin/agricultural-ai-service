from flask import Blueprint

from .controller import (
    detect_controller,
    classify_controller,
    get_versions_controller,
    upload_model_controller,
    update_model_controller,
    delete_model_controller,
    get_detect_result_controller,
    get_classify_result_controller,
    create_upload_task_controller,
    upload_chunk_controller,
    merge_chunks_controller,
)
from common.utils.jwt_utils import apply_auth_decorators

ai_bp = Blueprint("ai", __name__)

# 获取可用模型版本
ai_bp.route("/versions", methods=["GET"])(
    apply_auth_decorators("user", "admin", "expert")(get_versions_controller)
)

# 检测模型路由
ai_bp.route("/detect/<model_name>/<version>", methods=["POST"])(
    apply_auth_decorators("user", "admin", "expert")(detect_controller)
)
ai_bp.route("/detect/result/<task_id>", methods=["GET"])(
    apply_auth_decorators("user", "admin", "expert")(get_detect_result_controller)
)

# 分类模型路由
ai_bp.route("/classify/<model_name>/<version>", methods=["POST"])(
    apply_auth_decorators("user", "admin", "expert")(classify_controller)
)
ai_bp.route("/classify/result/<task_id>", methods=["GET"])(
    apply_auth_decorators("user", "admin", "expert")(get_classify_result_controller)
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
ai_bp.route("/models/version/<int:version_id>", methods=["DELETE"])(
    apply_auth_decorators("admin", "expert")(delete_model_controller)
)

# 分片上传相关路由
ai_bp.route("/upload/create", methods=["POST"])(
    apply_auth_decorators("admin", "expert")(create_upload_task_controller)
)

ai_bp.route("/upload/chunk", methods=["POST"])(
    apply_auth_decorators("admin", "expert")(upload_chunk_controller)
)

ai_bp.route("/upload/merge", methods=["POST"])(
    apply_auth_decorators("admin", "expert")(merge_chunks_controller)
)
