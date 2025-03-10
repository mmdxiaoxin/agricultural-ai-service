from .base_model import ClassifyYOLOModel
from ..enum import ModelWeights


class YOLOv11Classifier(ClassifyYOLOModel):
    """专注于分类任务的 YOLO11 模型"""

    def __init__(self, params=None):
        super().__init__(ModelWeights.YOLO11_CLASSIFY.value, params)
