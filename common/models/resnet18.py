from typing import Dict, List, Optional, Union, Any
import torch
from ultralytics import YOLO
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import io
import torchvision.transforms as transforms

from common.utils.exceptions import ModelError
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)

# 确定设备
device = "cuda:0" if torch.cuda.is_available() else "cpu"


class ResNetModel:
    """ResNet模型基类

    专注于使用ResNet进行图像分类的模型类，支持pytorch下的ResNet各个版本
    """

    def __init__(
        self, model_path: Union[str, Path], params: Optional[Dict[str, Any]] = None
    ):
        """
        初始化ResNet模型

        Args:
            model_path: 模型路径
            params: 初始化参数

        Raises:
            ModelError: 当模型加载失败时抛出
        """
        try:
            logger.info(f"开始初始化ResNet模型，路径: {model_path}")
            self.model_path = Path(model_path)
            if not self.model_path.exists():
                logger.error(f"模型文件不存在: {model_path}")
                raise FileNotFoundError(f"模型文件不存在: {model_path}")
            logger.info(f"模型文件存在，大小: {self.model_path.stat().st_size} 字节")

            # 默认参数
            self.default_params = {
                "device": device,
                "half": True if device != "cpu" else False,
                "img_size": 256,
            }

            # 合并默认参数和传入的参数
            self.params = self.default_params.copy()
            if params:
                self.params.update(params)
            logger.info(f"模型参数: {self.params}")

            # 加载模型
            logger.info("开始加载ResNet模型...")
            import torch
            import torch.nn as nn
            import torchvision.models as models

            # 加载模型权重
            checkpoint = torch.load(
                str(self.model_path), map_location=self.params["device"]
            )

            # 获取类别数量
            num_classes = checkpoint["model_state_dict"]["fc.weight"].size(0)
            logger.info(f"模型类别数量: {num_classes}")

            # 创建ResNet18模型实例
            self.model = models.resnet18(weights=None)
            self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)

            # 加载模型权重
            self.model.load_state_dict(checkpoint["model_state_dict"])

            # 设置为评估模式
            self.model.eval()

            # 移动到指定设备
            self.model = self.model.to(self.params["device"])

            # 如果使用半精度
            if self.params.get("half", False) and self.params["device"] != "cpu":
                self.model = self.model.half()

            # 设置图像预处理
            self.transform = transforms.Compose(
                [
                    transforms.Resize(
                        (self.params["img_size"], self.params["img_size"])
                    ),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                    ),
                ]
            )

            # 获取类别映射
            self.classes = checkpoint.get("classes", None)
            if self.classes:
                logger.info(f"加载类别映射，共 {len(self.classes)} 个类别")

            logger.info(f"成功加载ResNet模型: {model_path}")

        except Exception as e:
            logger.error(f"ResNet模型加载失败: {str(e)}", exc_info=True)
            raise ModelError(f"ResNet模型加载失败: {str(e)}")

    def predict(
        self, image_data: Union[bytes, List[bytes]], batch_size: int = 1, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        进行推理，支持单张图片和批量图片

        Args:
            image_data: 输入图片（二进制）或图片列表
            batch_size: 批处理大小
            **kwargs: 额外的推理参数

        Returns:
            ResNet 推理结果

        Raises:
            ModelError: 当推理过程出错时抛出
        """
        try:
            logger.info("开始ResNet模型推理...")
            # 合并默认参数和传入的参数
            predict_params = self.params.copy()
            predict_params.update(kwargs)
            logger.info(f"推理参数: {predict_params}")

            results = []
            # 处理单张或多张图片
            if isinstance(image_data, list):
                # 批量处理
                logger.info(f"批量处理 {len(image_data)} 张图片...")
                for i in range(0, len(image_data), batch_size):
                    batch = image_data[i : i + batch_size]
                    logger.info(f"处理批次 {i//batch_size + 1}, 大小: {len(batch)}")

                    batch_tensors = []
                    for img_bytes in batch:
                        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                        img_tensor = self.transform(img)
                        batch_tensors.append(img_tensor)

                    # 堆叠为批次
                    input_batch = torch.stack(batch_tensors).to(
                        predict_params["device"]
                    )

                    # 如果使用半精度
                    if (
                        predict_params.get("half", False)
                        and predict_params["device"] != "cpu"
                    ):
                        input_batch = input_batch.half()

                    # 推理
                    with torch.no_grad():
                        outputs = self.model(input_batch)
                        probabilities = torch.nn.functional.softmax(outputs, dim=1)
                        predicted_probs, predicted_classes = torch.max(probabilities, 1)

                        # 处理每张图片的结果
                        for prob, class_idx in zip(predicted_probs, predicted_classes):
                            class_idx = class_idx.item()
                            prob = prob.item()

                            # 获取类别名称
                            if self.classes:
                                class_name = self.classes[class_idx]
                            else:
                                class_name = f"Class_{class_idx}"

                            result = {
                                "class": class_idx,
                                "class_name": class_name,
                                "probability": prob,
                                "type": "resnet18",
                            }
                            results.append(result)
            else:
                # 单张图片处理
                logger.info("处理单张图片...")
                img = Image.open(io.BytesIO(image_data)).convert("RGB")
                img_tensor = self.transform(img)
                img_tensor = img_tensor.unsqueeze(0).to(predict_params["device"])  # type: ignore

                # 如果使用半精度
                if (
                    predict_params.get("half", False)
                    and predict_params["device"] != "cpu"
                ):
                    img_tensor = img_tensor.half()

                # 推理
                with torch.no_grad():
                    outputs = self.model(img_tensor)
                    probabilities = torch.nn.functional.softmax(outputs, dim=1)
                    predicted_prob, predicted_class = torch.max(probabilities, 1)

                    # 获取预测结果
                    class_idx = predicted_class.item()
                    prob = predicted_prob.item()

                    # 获取类别名称
                    if self.classes:
                        class_name = self.classes[class_idx]
                    else:
                        class_name = f"Class_{class_idx}"

                    result = {
                        "class": class_idx,
                        "class_name": class_name,
                        "confidence": prob,
                        "type": "classify",
                    }
                    results.append(result)

            logger.info(f"ResNet推理完成，结果数量: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"ResNet推理过程出错: {str(e)}", exc_info=True)
            raise ModelError(f"ResNet推理过程出错: {str(e)}")

    def classify(
        self, image_data: Union[bytes, List[bytes]], batch_size: int = 1
    ) -> List[Dict[str, Any]]:
        """
        进行分类推理，支持单张图片和批量图片

        Args:
            image_data: 输入图片（二进制）或图片列表
            batch_size: 批处理大小

        Returns:
            解析后的分类结果列表
        """
        return self.predict(image_data, batch_size)

    def update_params(self, **kwargs) -> None:
        """
        动态更新模型参数

        Args:
            **kwargs: 要更新的参数

        Raises:
            ModelError: 当参数更新失败时抛出
        """
        try:
            self.params.update(kwargs)
            logger.info(f"成功更新ResNet模型参数: {kwargs}")
        except Exception as e:
            logger.error(f"参数更新失败: {str(e)}")
            raise ModelError(f"参数更新失败: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            包含模型信息的字典
        """
        return {
            "model_path": str(self.model_path),
            "parameters": self.params,
            "type": "resnet18",
            "num_classes": len(self.classes) if self.classes else None,
        }
