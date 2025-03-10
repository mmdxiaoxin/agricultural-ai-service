from .base_model import BaseYOLOModel
from common.enum import ModelWeights


class YOLOv8Model(BaseYOLOModel):
    """YOLOv8 模型封装"""

    def __init__(self, model_path=None, params=None):
        super().__init__(model_path or ModelWeights.YOLO8_DETECT.value, params)
