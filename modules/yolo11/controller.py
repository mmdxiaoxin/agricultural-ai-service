from flask import request, jsonify

from .service import plant_classify_service


def plant_classify_controller():
    """
    接收植物图像，进行分类推理，返回推理结果。
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    # 获取图片文件
    image_file = request.files["image"]

    try:
        # 调用服务层进行推理
        image_data = image_file.read()
        result = plant_classify_service(image_data)

        # 返回推理结果
        return jsonify({"predictions": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
