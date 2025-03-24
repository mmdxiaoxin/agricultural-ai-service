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


class DetectYOLOModel(BaseYOLOModel):
    """专注于目标检测任务的模型"""

    def __init__(self, model_path=None, params=None):
        super().__init__(model_path, params)

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
        解析推理结果，返回包含 bbox 对象的结果
        :param results: YOLO 推理结果
        :return: 解析后的结果
        """
        parsed_results = []  # 初始化结果列表
        for result in results:
            boxes = result.boxes
            names = result.names
            for box in boxes:
                class_id = int(box.cls.cpu())
                bbox_list = (
                    box.xyxy.cpu().squeeze().tolist()
                )  # 获取 [xmin, ymin, xmax, ymax]
                # 转换为整数
                bbox_list = [int(coord) for coord in bbox_list]
                x = bbox_list[0]
                y = bbox_list[1]
                width = bbox_list[2] - bbox_list[0]
                height = bbox_list[3] - bbox_list[1]
                result_item = {
                    "type": "detect",
                    "class_name": names[class_id],
                    "confidence": box.conf.cpu().squeeze().item(),
                    "bbox": {
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height,
                    },
                    "class_id": class_id,
                }
                parsed_results.append(result_item)

        return parsed_results


class ClassifyYOLOModel(BaseYOLOModel):
    """专注于目标分类任务的模型"""

    def __init__(self, model_path=None, params=None):
        super().__init__(model_path, params)

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
            top1_label = result.names[top1_index]
            # 获取对应的最高置信度
            top1_confidence = result.probs.top1conf.item()
            result_info = {
                "type": "classify",
                "class_id": top1_index,
                "class_name": top1_label,
                "confidence": top1_confidence,  # 置信度
            }
            parsed_results.append(result_info)
        return parsed_results
