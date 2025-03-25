import logging
from flask import request, jsonify
from werkzeug.exceptions import RequestEntityTooLarge

from .service import plant_detect_service

logger = logging.getLogger(__name__)

# 设置最大请求大小为16MB
MAX_CONTENT_LENGTH = 16 * 1024 * 1024


def plant_detect_controller():
    """
    接收植物图像，进行分类推理，返回推理结果。
    """
    try:
        # 检查请求大小
        if request.content_length and request.content_length > MAX_CONTENT_LENGTH:
            return jsonify({"error": "文件大小超过限制（最大16MB）"}), 413

        if "image" not in request.files:
            return jsonify({"error": "未提供图片文件"}), 400

        # 获取图片文件
        image_file = request.files["image"]
        if not image_file.filename:
            return jsonify({"error": "未选择文件"}), 400

        # 检查文件类型
        if not image_file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            return jsonify({"error": "不支持的文件类型，仅支持PNG和JPG格式"}), 400

        # 调用服务层进行推理
        image_data = image_file.read()
        result = plant_detect_service(image_data)

        # 返回推理结果
        return jsonify({"predictions": result}), 200

    except RequestEntityTooLarge:
        logger.error("请求文件过大")
        return jsonify({"error": "文件大小超过限制（最大16MB）"}), 413
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return jsonify({"error": f"服务器内部错误: {str(e)}"}), 500
