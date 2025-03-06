from ultralytics import YOLO
from PIL import Image
import io
import numpy as np
import torch
from ultralytics.engine.results import Probs

from common.constant import disease_mapping
from common.enum import ModelWeights

device = "cuda:0" if torch.cuda.is_available() else "cpu"
model_path = ModelWeights.YOLO11_BEST.value
ini_params = {
    "device": device,  # 设备类型
    "conf": 0.25,  # 物体置信度阈值
    "iou": 0.5,  # 用于非极大值抑制的IOU阈值
    "classes": None,  # 类别过滤器
    "verbose": False,
}


def parse_classify_results(results):
    """
    解析推理结果，提取有用的信息（仅分类任务）
    :param results: YOLO 推理结果
    :return: 解析后的结果，包含类别标签、置信度等
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

        print(parsed_results)
    return parsed_results


def _preprocess_image(image_data):
    """
    预处理输入图像数据
    :param image_data: 输入的图像数据（bytes类型）
    :return: 处理后的 PIL 图像
    """
    # 将图片数据转换为 PIL 图像
    image = Image.open(io.BytesIO(image_data))
    return image


class YOLO11Model:
    def __init__(self, params=None):
        """
        初始化 YOLO11 模型，并加载权重
        :param params: YOLO的配置参数
        """
        self.model = YOLO(model_path, params if params else ini_params)

    def predict(self, image_data):
        """
        使用 YOLO 对图像进行推理，返回推理结果
        :param image_data: 输入的图片数据，类型为 bytes
        :return: 推理结果（包含标签、置信度、坐标等）
        """
        image = _preprocess_image(image_data)
        results = self.model(image)
        return results

    def save_model(self, save_path):
        """
        保存训练后的模型到指定路径
        :param save_path: 保存路径
        """
        self.model.save(save_path)

    def load_model(self, model_path):
        """
        加载指定路径的模型
        :param model_path: 模型路径
        """
        self.model = YOLO(model_path)

    def visualize_results(self, image_data, results):
        """
        可视化推理结果，显示预测框和标签
        :param image_data: 输入图像数据
        :param results: 推理结果
        """
        image = _preprocess_image(image_data)
        image.show()  # 显示原图
        # 对于每个结果，绘制预测框和标签
        for result in results:
            for label, confidence, box in zip(result.names, result.conf, result.xywh):
                # 可视化绘制（此处为伪代码，可根据需要使用OpenCV或其他库绘制）
                self.draw_bbox(image, box, label, confidence)

        image.show()

    def draw_bbox(self, image, bbox, label, confidence):
        """
        在图像上绘制预测框和标签
        :param image: 输入图像
        :param bbox: 预测框坐标
        :param label: 类别标签
        :param confidence: 置信度
        """
        # 使用 PIL 或 OpenCV 绘制框和标签
        pass
