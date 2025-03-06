import json
import io
from PIL import Image
from common.models.YOLO11Model import YOLO11Model, parse_classify_results

# 获取模型的绝对路径
model = YOLO11Model()


def plant_classify_service(image_data):
    """
    使用 YOLO 对图像进行推理，返回分类结果的序列化数据。

    :param image_data: 输入的图片数据，类型为 bytes
    :return: 序列化的推理结果
    """

    results = model.predict(image_data)
    # return results[0].names[results[0].probs.top1]
    result = parse_classify_results(results)
    return result
