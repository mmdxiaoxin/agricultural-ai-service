from flask import Blueprint, render_template, request, jsonify, send_from_directory
from .controllers.model_controller import (
    get_models,
    get_model,
    create_model,
    update_model,
    delete_model,
)

manage_bp = Blueprint(
    "manage",
    __name__,
    template_folder="views",
    static_folder="static",
    static_url_path="/manage/static",
)


# 页面路由
@manage_bp.route("/")
def index():
    """模型管理首页"""
    return render_template("index.html")


@manage_bp.route("/favicon.ico")
def favicon():
    """网站图标"""
    return send_from_directory("static", "favicon.ico")


@manage_bp.route("/models")
def model_list():
    """模型列表页"""
    return render_template("models/list.html")


@manage_bp.route("/models/create")
def model_create():
    """创建模型页"""
    return render_template("models/create.html")


@manage_bp.route("/models/<int:model_id>")
def model_detail(model_id):
    """模型详情页"""
    return render_template("models/detail.html", model_id=model_id)


@manage_bp.route("/models/<int:model_id>/edit")
def model_edit(model_id):
    """编辑模型页"""
    return render_template("models/edit.html", model_id=model_id)


# API路由
@manage_bp.route("/api/models", methods=["GET"])
def api_get_models():
    """获取模型列表API"""
    response, status_code = get_models()
    return response, status_code


@manage_bp.route("/api/models/<int:model_id>", methods=["GET"])
def api_get_model(model_id):
    """获取模型详情API"""
    response, status_code = get_model(model_id)
    return response, status_code


@manage_bp.route("/api/models", methods=["POST"])
def api_create_model():
    """创建模型API"""
    data = request.get_json()
    response, status_code = create_model(data)
    return response, status_code


@manage_bp.route("/api/models/<int:model_id>", methods=["PUT"])
def api_update_model(model_id):
    """更新模型API"""
    data = request.get_json()
    response, status_code = update_model(model_id, data)
    return response, status_code


@manage_bp.route("/api/models/<int:model_id>", methods=["DELETE"])
def api_delete_model(model_id):
    """删除模型API"""
    response, status_code = delete_model(model_id)
    return response, status_code
