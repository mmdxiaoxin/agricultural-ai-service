from common.models.base_model import BaseYOLOModel
from common.enum import ModelWeights


class YOLOv5Model(BaseYOLOModel):
    """YOLOv5 模型封装"""

    def __init__(self, model_path=None, params=None):
        super().__init__(model_path or ModelWeights.YOLO5_DETECT.value, params)
