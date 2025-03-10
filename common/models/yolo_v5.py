from common.enum import ModelWeights
from common.models.base_model import DetectYOLOModel


class YOLOv5Detector(DetectYOLOModel):
    """YOLOv5 模型封装"""

    def __init__(self, params=None):
        super().__init__(ModelWeights.YOLO5_DETECT.value, params)
