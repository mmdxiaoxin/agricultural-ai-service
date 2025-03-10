from common.enum import ModelWeights
from .base_model import BaseYOLOModel


class YOLOv8Detector(BaseYOLOModel):
    """YOLOv8 模型封装"""

    def __init__(self, model_path=None, params=None):
        super().__init__(model_path or ModelWeights.YOLO8_DETECT.value, params)

    def detect(self, image_data):
        """
        进行目标检测
        :param image_data: 输入图片（二进制）
        :return: 解析后的类别和置信度
        """
        results = self.predict(image_data)
        return self._parse_detect_results(results)

    def _parse_detect_results(self, results):
        """
        解析推理结果
        :param results: YOLO 推理结果
        :return: 解析后的结果
        """
        parsed_results = []  # 初始化结果列表
        for result in results:
            boxes = result.boxes
            names = result.names
            for box in boxes:
                class_id = int(box.cls.cpu())
                bbox = box.xyxy.cpu().squeeze().tolist()
                bbox = [int(coord) for coord in bbox]  # 转换边界框坐标为整数
                result = {
                    "class_name": names[class_id],  # 类别名称
                    "confidence": box.conf.cpu().squeeze().item(),  # 置信度
                    "bbox": bbox,  # 边界框
                    "class_id": class_id,  # 类别ID
                }
                parsed_results.append(result)

        return parsed_results  # 返回结果列表
