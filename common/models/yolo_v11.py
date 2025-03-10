from common.constant import disease_mapping
from .base_model import BaseYOLOModel
from ..enum import ModelWeights


class YOLOv11Classifier(BaseYOLOModel):
    """专注于分类任务的 YOLO11 模型"""

    def __init__(self, model_path=None, params=None):
        super().__init__(model_path or ModelWeights.YOLO11_CLASSIFY.value, params)

    def classify(self, image_data):
        """
        进行分类推理
        :param image_data: 输入图片（二进制）
        :return: 解析后的类别和置信度
        """
        results = self.predict(image_data)
        return self._parse_classify_results(results)

    def _parse_classify_results(self, results):
        """
        解析推理结果
        :param results: YOLO 推理结果
        :return: 解析后的结果
        """
        parsed_results = []
        for result in results:
            # 获取最高概率的类别索引（top1）
            top1_index = result.probs.top1

            # 获取对应的中文标签
            top1_label = disease_mapping.get(result.names[top1_index], "未知疾病")

            # 获取对应的最高置信度
            top1_confidence = result.probs.top1conf.item()

            result_info = {
                "class_name": top1_label,
                "confidence": top1_confidence,  # 置信度
            }
            parsed_results.append(result_info)
        return parsed_results
