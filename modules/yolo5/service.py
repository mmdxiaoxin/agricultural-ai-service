from common.models import YOLOv5Detector

model = YOLOv5Detector()


def plant_detect_service(image_data):
    """
    使用 YOLO 对图像进行推理，返回分类结果的序列化数据。
    :param image_data: 输入的图片数据，类型为 bytes
    :return: 序列化的推理结果
    """
    results = model.detect(image_data)
    return results
