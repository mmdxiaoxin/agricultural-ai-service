import torch
from ultralytics import YOLO

from common.utils.image_processing import ImageProcessor

# 确定设备
device = "cuda:0" if torch.cuda.is_available() else "cpu"

# 统一的默认参数
DEFAULT_YOLO_PARAMS = {
    "device": device,
    "conf": 0.25,
    "iou": 0.5,
    "classes": None,
    "verbose": False,
}


class BaseYOLOModel:
    """YOLO 模型基类"""

    def __init__(self, model_path, params=None):
        """
        初始化 YOLO 模型
        :param model_path: 模型路径
        :param params: YOLO 初始化参数
        """
        self.model_path = model_path
        self.params = params or DEFAULT_YOLO_PARAMS
        self.model = YOLO(self.model_path, self.params)

    def predict(self, image_data):
        """
        进行推理
        :param image_data: 输入图片（二进制）
        :return: YOLO 推理结果
        """
        image = ImageProcessor.preprocess(image_data)
        return self.model(image)

    def update_params(self, **kwargs):
        """动态更新模型参数"""
        self.params.update(kwargs)
        self.model = YOLO(self.model_path, self.params)

    def save_model(self, save_path):
        """保存训练后的模型"""
        self.model.save(save_path)

    def load_model(self, model_path):
        """加载新模型"""
        self.model_path = model_path
        self.model = YOLO(model_path, self.params)
