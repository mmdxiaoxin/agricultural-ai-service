from common.enum import ModelWeights
from .base_model import DetectYOLOModel


class YOLOv8Detector(DetectYOLOModel):
    """YOLOv8 模型封装"""

    def __init__(self, params=None):
        super().__init__(ModelWeights.YOLO8_DETECT.value, params)
