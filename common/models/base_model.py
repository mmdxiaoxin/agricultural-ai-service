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

# 统一的默认参数
DEFAULT_YOLO_PARAMS = {
    "device": device,
    "conf": 0.25,
    "iou": 0.5,
    "classes": None,
    "verbose": False,
    "half": True,  # 使用半精度推理
    "agnostic_nms": False,  # 类别无关的NMS
    "max_det": 300,  # 最大检测框数量
}


def bytes_to_numpy(image_bytes: bytes) -> np.ndarray:
    """将图片bytes转换为numpy数组

    Args:
        image_bytes: 图片二进制数据

    Returns:
        numpy数组格式的图片数据
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


class BaseYOLOModel:
    """YOLO 模型基类

    提供基础的YOLO模型功能，包括模型加载、推理、参数更新等。
    支持单张图片和批量图片处理。
    """

    def __init__(
        self, model_path: Union[str, Path], params: Optional[Dict[str, Any]] = None
    ):
        """
        初始化 YOLO 模型

        Args:
            model_path: 模型路径
            params: YOLO 初始化参数

        Raises:
            ModelError: 当模型加载失败时抛出
        """
        try:
            logger.info(f"开始初始化YOLO模型，路径: {model_path}")
            self.model_path = Path(model_path)
            if not self.model_path.exists():
                logger.error(f"模型文件不存在: {model_path}")
                raise FileNotFoundError(f"模型文件不存在: {model_path}")
            logger.info(f"模型文件存在，大小: {self.model_path.stat().st_size} 字节")

            self.params = params or DEFAULT_YOLO_PARAMS.copy()
            logger.info(f"模型参数: {self.params}")

            logger.info("开始加载YOLO模型...")
            self.model = YOLO(str(self.model_path))
            logger.info(f"成功加载模型: {model_path}")
            logger.info(f"模型设备: {self.model.device}")
            logger.info(f"模型任务类型: {self.model.task}")

        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}", exc_info=True)
            raise ModelError(f"模型加载失败: {str(e)}")

    def predict(
        self, image_data: Union[bytes, List[bytes]], batch_size: int = 1, **kwargs
    ) -> Any:
        """
        进行推理，支持单张图片和批量图片

        Args:
            image_data: 输入图片（二进制）或图片列表
            batch_size: 批处理大小
            **kwargs: 额外的推理参数

        Returns:
            YOLO 推理结果

        Raises:
            ModelError: 当推理过程出错时抛出
        """
        try:
            logger.info("开始模型推理...")
            # 合并默认参数和传入的参数
            predict_params = self.params.copy()
            predict_params.update(kwargs)
            logger.info(f"推理参数: {predict_params}")

            if isinstance(image_data, list):
                # 批量处理
                logger.info("开始批量处理...")
                results = []
                for i in range(0, len(image_data), batch_size):
                    batch = image_data[i : i + batch_size]
                    logger.info(f"处理批次 {i//batch_size + 1}, 大小: {len(batch)}")
                    # 将bytes转换为numpy数组
                    batch_images = [bytes_to_numpy(img) for img in batch]
                    batch_results = self.model(batch_images, **predict_params)
                    results.extend(batch_results)
                logger.info(f"批量处理完成，共 {len(results)} 个结果")
                return results
            else:
                # 单张图片处理
                logger.info("开始单张图片处理...")
                # 将bytes转换为numpy数组
                image = bytes_to_numpy(image_data)
                result = self.model(image, **predict_params)
                logger.info("单张图片处理完成")
                return result

        except Exception as e:
            logger.error(f"推理过程出错: {str(e)}", exc_info=True)
            raise ModelError(f"推理过程出错: {str(e)}")

    def update_params(self, **kwargs) -> None:
        """
        动态更新模型参数

        Args:
            **kwargs: 要更新的参数

        Raises:
            ModelError: 当参数更新失败时抛出
        """
        try:
            # 验证参数
            for key, value in kwargs.items():
                if key not in DEFAULT_YOLO_PARAMS:
                    logger.warning(f"未知参数: {key}")

            self.params.update(kwargs)
            logger.info(f"成功更新模型参数: {kwargs}")

        except Exception as e:
            logger.error(f"参数更新失败: {str(e)}")
            raise ModelError(f"参数更新失败: {str(e)}")

    def save_model(self, save_path: Union[str, Path]) -> None:
        """
        保存训练后的模型

        Args:
            save_path: 保存路径

        Raises:
            ModelError: 当保存失败时抛出
        """
        try:
            save_path = Path(save_path)
            self.model.save(str(save_path))
            logger.info(f"模型已保存到: {save_path}")

        except Exception as e:
            logger.error(f"模型保存失败: {str(e)}")
            raise ModelError(f"模型保存失败: {str(e)}")

    def load_model(self, model_path: Union[str, Path]) -> None:
        """
        加载新模型

        Args:
            model_path: 新模型路径

        Raises:
            ModelError: 当加载失败时抛出
        """
        try:
            model_path = Path(model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"模型文件不存在: {model_path}")

            self.model_path = model_path
            self.model = YOLO(str(model_path))
            logger.info(f"成功加载新模型: {model_path}")

        except Exception as e:
            logger.error(f"新模型加载失败: {str(e)}")
            raise ModelError(f"新模型加载失败: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            包含模型信息的字典
        """
        return {
            "model_path": str(self.model_path),
            "parameters": self.params,
            "device": self.model.device,
            "task": self.model.task,
        }


class DetectYOLOModel(BaseYOLOModel):
    """专注于目标检测任务的模型"""

    def __init__(
        self,
        model_path: Union[str, Path],
        params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(model_path, params)

    def detect(
        self, image_data: Union[bytes, List[bytes]], batch_size: int = 1
    ) -> List[Dict[str, Any]]:
        """
        进行目标检测，支持单张图片和批量图片

        Args:
            image_data: 输入图片（二进制）或图片列表
            batch_size: 批处理大小

        Returns:
            解析后的检测结果列表
        """
        try:
            logger.info("开始目标检测...")
            logger.info(f"输入数据类型: {type(image_data)}")
            if isinstance(image_data, list):
                logger.info(f"批量处理，图片数量: {len(image_data)}")
            else:
                logger.info(f"单张图片处理，大小: {len(image_data)} 字节")

            results = self.predict(image_data, batch_size)
            logger.info(f"推理完成，结果类型: {type(results)}")

            parsed_results = self._parse_detect_results(results)
            logger.info(f"解析完成，检测到 {len(parsed_results)} 个目标")
            return parsed_results

        except Exception as e:
            logger.error(f"目标检测失败: {str(e)}", exc_info=True)
            raise ModelError(f"目标检测失败: {str(e)}")

    def _parse_detect_results(self, results: List[Any]) -> List[Dict[str, Any]]:
        """
        解析推理结果，返回包含 bbox 对象的结果

        Args:
            results: YOLO 推理结果

        Returns:
            解析后的结果列表
        """
        parsed_results = []
        for result in results:
            boxes = result.boxes
            names = result.names
            for box in boxes:
                class_id = int(box.cls.cpu())
                bbox_list = box.xyxy.cpu().squeeze().tolist()
                bbox_list = [int(coord) for coord in bbox_list]

                result_item = {
                    "type": "detect",
                    "class_name": names[class_id],
                    "confidence": float(box.conf.cpu().squeeze().item()),
                    "bbox": {
                        "x": bbox_list[0],
                        "y": bbox_list[1],
                        "width": bbox_list[2] - bbox_list[0],
                        "height": bbox_list[3] - bbox_list[1],
                    },
                    "class_id": class_id,
                    "area": (bbox_list[2] - bbox_list[0])
                    * (bbox_list[3] - bbox_list[1]),
                }
                parsed_results.append(result_item)
        return parsed_results


class ClassifyYOLOModel(BaseYOLOModel):
    """专注于目标分类任务的模型"""

    def __init__(
        self,
        model_path: Union[str, Path],
        params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(model_path, params)

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
        results = self.predict(image_data, batch_size)
        return self._parse_classify_results(results)

    def _parse_classify_results(self, results: List[Any]) -> List[Dict[str, Any]]:
        """
        解析推理结果

        Args:
            results: YOLO 推理结果

        Returns:
            解析后的结果列表
        """
        parsed_results = []
        for result in results:
            top1_index = result.probs.top1
            top1_label = result.names[top1_index]
            top1_confidence = result.probs.top1conf.item()

            # 获取前5个最可能的类别
            top5_indices = result.probs.top5
            top5_confidences = result.probs.top5conf.tolist()
            top5_labels = [result.names[i] for i in top5_indices]

            result_info = {
                "type": "classify",
                "class_id": top1_index,
                "class_name": top1_label,
                "confidence": float(top1_confidence),
                "top5": [
                    {"class_name": label, "confidence": float(conf)}
                    for label, conf in zip(top5_labels, top5_confidences)
                ],
            }
            parsed_results.append(result_info)
        return parsed_results


class BaseResNetModel:
    """ResNet 模型基类"""

    def __init__(
        self, model_path: Union[str, Path], params: Optional[Dict[str, Any]] = None
    ):
        """
        初始化 ResNet 模型

        Args:
            model_path: 模型路径
            params: 模型参数

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

            self.params = params or {}
            logger.info(f"模型参数: {self.params}")

            logger.info("开始加载ResNet模型...")
            self.model = torch.load(str(self.model_path))
            self.model.eval()  # 设置为评估模式
            if torch.cuda.is_available():
                self.model = self.model.cuda()
            logger.info(f"成功加载模型: {model_path}")
            logger.info(f"模型设备: {next(self.model.parameters()).device}")

        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}", exc_info=True)
            raise ModelError(f"模型加载失败: {str(e)}")

    def predict(
        self, image_data: Union[bytes, List[bytes]], batch_size: int = 1, **kwargs
    ) -> Any:
        """
        进行推理，支持单张图片和批量图片

        Args:
            image_data: 输入图片（二进制）或图片列表
            batch_size: 批处理大小
            **kwargs: 额外的推理参数

        Returns:
            推理结果

        Raises:
            ModelError: 当推理过程出错时抛出
        """
        try:
            logger.info("开始模型推理...")
            # 合并默认参数和传入的参数
            predict_params = self.params.copy()
            predict_params.update(kwargs)
            logger.info(f"推理参数: {predict_params}")

            if isinstance(image_data, list):
                # 批量处理
                logger.info("开始批量处理...")
                results = []
                for i in range(0, len(image_data), batch_size):
                    batch = image_data[i : i + batch_size]
                    logger.info(f"处理批次 {i//batch_size + 1}, 大小: {len(batch)}")
                    # 将bytes转换为numpy数组
                    batch_images = [bytes_to_numpy(img) for img in batch]
                    batch_results = self._process_batch(batch_images, **predict_params)
                    results.extend(batch_results)
                logger.info(f"批量处理完成，共 {len(results)} 个结果")
                return results
            else:
                # 单张图片处理
                logger.info("开始单张图片处理...")
                # 将bytes转换为numpy数组
                image = bytes_to_numpy(image_data)
                result = self._process_single(image, **predict_params)
                logger.info("单张图片处理完成")
                return result

        except Exception as e:
            logger.error(f"推理过程出错: {str(e)}", exc_info=True)
            raise ModelError(f"推理过程出错: {str(e)}")

    def _process_single(self, image: np.ndarray, **kwargs) -> torch.Tensor:
        """处理单张图片"""
        # 转换为tensor
        image_tensor = torch.from_numpy(image).float()
        image_tensor = image_tensor.permute(2, 0, 1)  # HWC to CHW
        image_tensor = image_tensor.unsqueeze(0)  # 添加batch维度
        if torch.cuda.is_available():
            image_tensor = image_tensor.cuda()

        with torch.no_grad():
            output = self.model(image_tensor)
        return output

    def _process_batch(self, images: List[np.ndarray], **kwargs) -> List[torch.Tensor]:
        """处理批量图片"""
        # 转换为tensor
        batch = torch.stack(
            [torch.from_numpy(img).float().permute(2, 0, 1) for img in images]
        )
        if torch.cuda.is_available():
            batch = batch.cuda()

        with torch.no_grad():
            outputs = self.model(batch)
        return outputs

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
            logger.info(f"成功更新模型参数: {kwargs}")
        except Exception as e:
            logger.error(f"参数更新失败: {str(e)}")
            raise ModelError(f"参数更新失败: {str(e)}")

    def save_model(self, save_path: Union[str, Path]) -> None:
        """
        保存训练后的模型

        Args:
            save_path: 保存路径

        Raises:
            ModelError: 当保存失败时抛出
        """
        try:
            save_path = Path(save_path)
            torch.save(self.model.state_dict(), str(save_path))
            logger.info(f"模型已保存到: {save_path}")
        except Exception as e:
            logger.error(f"模型保存失败: {str(e)}")
            raise ModelError(f"模型保存失败: {str(e)}")

    def load_model(self, model_path: Union[str, Path]) -> None:
        """
        加载新模型

        Args:
            model_path: 新模型路径

        Raises:
            ModelError: 当加载失败时抛出
        """
        try:
            model_path = Path(model_path)
            if not model_path.exists():
                raise FileNotFoundError(f"模型文件不存在: {model_path}")

            self.model_path = model_path
            self.model = torch.load(str(model_path))
            self.model.eval()
            if torch.cuda.is_available():
                self.model = self.model.cuda()
            logger.info(f"成功加载新模型: {model_path}")
        except Exception as e:
            logger.error(f"新模型加载失败: {str(e)}")
            raise ModelError(f"新模型加载失败: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息

        Returns:
            包含模型信息的字典
        """
        return {
            "model_path": str(self.model_path),
            "parameters": self.params,
            "device": self.model.device,
        }


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
                "img_size": 224,
            }

            # 合并默认参数和传入的参数
            self.params = self.default_params.copy()
            if params:
                self.params.update(params)
            logger.info(f"模型参数: {self.params}")

            # 加载模型
            logger.info("开始加载ResNet模型...")
            import torch
            import torchvision.models as models

            # 创建ResNet18模型实例
            self.model = models.resnet18(pretrained=False)

            # 加载模型权重
            state_dict = torch.load(
                str(self.model_path), map_location=self.params["device"]
            )
            self.model.load_state_dict(state_dict)

            # 设置为评估模式
            self.model.eval()

            # 移动到指定设备
            self.model = self.model.to(self.params["device"])

            # 如果使用半精度
            if self.params.get("half", False) and self.params["device"] != "cpu":
                self.model = self.model.half()

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

            # 导入必要的库
            import torch
            import torchvision.transforms as transforms
            from PIL import Image
            import io

            # 设置图像预处理
            preprocess = transforms.Compose(
                [
                    transforms.Resize(predict_params.get("img_size", 224)),
                    transforms.CenterCrop(predict_params.get("img_size", 224)),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                    ),
                ]
            )

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
                        img_tensor = preprocess(img)
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
                        output = self.model(input_batch)

                    # 处理每张图片的结果
                    for out in output:
                        # 获取预测结果
                        probabilities = torch.nn.functional.softmax(out, dim=0)
                        # 获取类别ID和对应概率
                        top5_prob, top5_indices = torch.topk(probabilities, 5)

                        result = {
                            "probs": probabilities,
                            "top5": top5_indices.cpu().numpy(),
                            "top5conf": top5_prob.cpu().numpy(),
                            "top1": top5_indices[0].item(),
                            "top1conf": top5_prob[0].item(),
                            "names": self.params.get("class_names", {}),  # 类别名称字典
                        }

                        results.append(result)
            else:
                # 单张图片处理
                logger.info("处理单张图片...")
                img: Image.Image = Image.open(io.BytesIO(image_data)).convert("RGB")
                img_tensor = torch.as_tensor(preprocess(img), dtype=torch.float32)
                img_tensor = torch.unsqueeze(img_tensor, 0).to(predict_params["device"])

                # 如果使用半精度
                if (
                    predict_params.get("half", False)
                    and predict_params["device"] != "cpu"
                ):
                    img_tensor = img_tensor.half()

                # 推理
                with torch.no_grad():
                    output = self.model(img_tensor)

                # 获取预测结果
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                # 获取类别ID和对应概率
                top5_prob, top5_indices = torch.topk(probabilities, 5)

                result = {
                    "probs": probabilities,
                    "top5": top5_indices.cpu().numpy(),
                    "top5conf": top5_prob.cpu().numpy(),
                    "top1": top5_indices[0].item(),
                    "top1conf": top5_prob[0].item(),
                    "names": self.params.get("class_names", {}),  # 类别名称字典
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
        results = self.predict(image_data, batch_size)
        return self._parse_resnet_results(results)

    def _parse_resnet_results(self, results: List[Any]) -> List[Dict[str, Any]]:
        """
        解析ResNet推理结果

        Args:
            results: ResNet 推理结果

        Returns:
            解析后的结果列表
        """
        parsed_results = []
        for result in results:
            top1_index = result["top1"]
            class_names = result["names"]
            top1_label = class_names.get(top1_index, f"class_{top1_index}")
            top1_confidence = float(result["top1conf"])

            # 获取前5个最可能的类别
            top5_indices = result["top5"]
            top5_confidences = result["top5conf"].tolist()
            top5_labels = [class_names.get(idx, f"class_{idx}") for idx in top5_indices]

            result_info = {
                "type": "resnet",
                "class_id": top1_index,
                "class_name": top1_label,
                "confidence": top1_confidence,
                "top5": [
                    {"class_name": label, "confidence": float(conf)}
                    for label, conf in zip(top5_labels, top5_confidences)
                ],
            }
            parsed_results.append(result_info)
        return parsed_results

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
            "type": "resnet",
        }
