from typing import Dict, List, Optional, Union, Any
import torch
from ultralytics import YOLO
from pathlib import Path
import numpy as np
import cv2
from PIL import Image
import io
import torchvision.transforms as transforms
import onnxruntime as ort

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
    支持PyTorch和ONNX格式。
    """

    def __init__(
        self,
        model_path: Union[str, Path],
        params: Optional[Dict[str, Any]] = None,
        session_options: Optional[Any] = None,
    ):
        """
        初始化 YOLO 模型

        Args:
            model_path: 模型路径
            params: YOLO 初始化参数
            session_options: ONNX Runtime会话选项

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

            # 保存会话选项
            self.session_options = session_options

            # 判断模型格式
            self.is_onnx = str(self.model_path).endswith(".onnx")
            if self.is_onnx:
                self._load_onnx_model()
            else:
                self._load_torch_model()

            logger.info(
                f"成功加载模型: {model_path} ({'ONNX' if self.is_onnx else 'PyTorch'})"
            )

        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}", exc_info=True)
            raise ModelError(f"模型加载失败: {str(e)}")

    def _load_onnx_model(self):
        """加载ONNX模型"""
        try:
            # 检查CUDA可用性并记录
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                logger.info(f"CUDA可用，使用GPU: {torch.cuda.get_device_name(0)}")
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            else:
                logger.info("CUDA不可用，将使用CPU进行推理")
                providers = ["CPUExecutionProvider"]

            try:
                # 创建ONNX运行时会话
                self.session = ort.InferenceSession(
                    str(self.model_path),
                    providers=providers,
                    sess_options=self.session_options,
                )
                logger.info(
                    f"ONNX模型加载成功，使用提供程序: {self.session.get_providers()}"
                )
            except Exception as e:
                logger.warning(f"使用GPU加载ONNX模型失败: {str(e)}，尝试使用CPU加载")
                # 强制使用CPU加载
                self.session = ort.InferenceSession(
                    str(self.model_path),
                    providers=["CPUExecutionProvider"],
                    sess_options=self.session_options,
                )
                logger.info("ONNX模型已切换到CPU设备")

            # 获取输入输出信息
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]

            # 获取输入形状
            self.input_shape = self.session.get_inputs()[0].shape
            logger.info(f"ONNX模型输入形状: {self.input_shape}")

            # 获取模型元数据
            self.metadata = self.session.get_modelmeta().custom_metadata_map
            logger.info(f"ONNX模型元数据: {self.metadata}")

            # 获取类别名称
            if "names" in self.metadata:
                self.class_names = eval(self.metadata["names"])
                logger.info(f"ONNX模型类别名称: {self.class_names}")
            else:
                self.class_names = None
                logger.warning("ONNX模型未定义类别名称")

        except Exception as e:
            logger.error(f"ONNX模型加载失败: {str(e)}", exc_info=True)
            raise ModelError(f"ONNX模型加载失败: {str(e)}")

    def _load_torch_model(self):
        """加载PyTorch模型"""
        try:
            logger.info("开始加载YOLO模型...")

            # 检查CUDA可用性并记录
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                logger.info(f"CUDA可用，使用GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("CUDA不可用，将使用CPU进行推理")
                # 更新设备参数为CPU
                self.params["device"] = "cpu"
                # 在CPU模式下禁用半精度
                self.params["half"] = False

            try:
                # 尝试使用指定设备加载模型
                self.model = YOLO(str(self.model_path))
                logger.info(f"模型设备: {self.model.device}")
                logger.info(f"模型任务类型: {self.model.task}")
            except Exception as e:
                logger.warning(f"使用指定设备加载模型失败: {str(e)}，尝试使用CPU加载")
                # 强制使用CPU加载
                self.params["device"] = "cpu"
                self.params["half"] = False
                self.model = YOLO(str(self.model_path))
                logger.info("模型已切换到CPU设备")

            # 验证模型是否成功加载到指定设备
            if self.params["device"] != "cpu" and self.model.device.type == "cpu":
                logger.warning("模型未能加载到GPU，已自动切换到CPU")
                self.params["device"] = "cpu"
                self.params["half"] = False

        except Exception as e:
            logger.error(f"PyTorch模型加载失败: {str(e)}", exc_info=True)
            raise ModelError(f"PyTorch模型加载失败: {str(e)}")

    def predict(
        self, image_data: Union[bytes, List[bytes]], batch_size: int = 1, **kwargs
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        进行推理，支持单张图片和批量图片

        Args:
            image_data: 输入图片（二进制）或图片列表
            batch_size: 批处理大小
            **kwargs: 额外的推理参数

        Returns:
            Union[List[Dict[str, Any]], Dict[str, Any]]: 批量处理时返回结果列表，单张图片时返回单个结果

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
                    if self.is_onnx:
                        batch_results = self._onnx_predict_batch(
                            batch_images, predict_params
                        )
                    else:
                        batch_results = self.model(batch_images, **predict_params)
                        # 确保结果是列表类型
                        if not isinstance(batch_results, list):
                            batch_results = [batch_results]
                    results.extend(batch_results)
                logger.info(f"批量处理完成，共 {len(results)} 个结果")
                return results
            else:
                # 单张图片处理
                logger.info("开始单张图片处理...")
                # 将bytes转换为numpy数组
                image = bytes_to_numpy(image_data)
                if self.is_onnx:
                    result = self._onnx_predict_single(image, predict_params)
                else:
                    result = self.model(image, **predict_params)
                logger.info("单张图片处理完成")
                return result

        except Exception as e:
            logger.error(f"推理过程出错: {str(e)}", exc_info=True)
            raise ModelError(f"推理过程出错: {str(e)}")

    def _onnx_predict_batch(
        self, images: List[np.ndarray], params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """ONNX批量推理"""
        try:
            # 预处理图像
            processed_images = []
            for img in images:
                # 调整图像大小
                img = cv2.resize(img, (self.input_shape[2], self.input_shape[3]))
                # 转换为RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                # 归一化
                img = img.astype(np.float32) / 255.0
                # 调整维度顺序 (H, W, C) -> (C, H, W)
                img = img.transpose(2, 0, 1)
                processed_images.append(img)

            # 堆叠为批次
            input_batch = np.stack(processed_images)

            # 推理
            outputs = self.session.run(
                self.output_names, {self.input_name: input_batch}
            )

            # 后处理结果
            results = []
            # 确保outputs[0]是numpy数组
            if isinstance(outputs[0], np.ndarray):
                for i in range(len(outputs[0])):
                    output = outputs[0][i]
                    # 解析检测结果
                    boxes = output[:, :4]  # 边界框
                    scores = output[:, 4]  # 置信度
                    class_ids = output[:, 5]  # 类别ID

                    # 应用NMS
                    indices = cv2.dnn.NMSBoxes(
                        boxes.tolist(),
                        scores.tolist(),
                        params["conf"],
                        params["iou"],
                    )

                    # 构建结果
                    result = {
                        "boxes": boxes[indices],
                        "scores": scores[indices],
                        "class_ids": class_ids[indices],
                    }
                    results.append(result)
            else:
                logger.warning("ONNX输出格式不符合预期")
                return []

            return results

        except Exception as e:
            logger.error(f"ONNX批量推理失败: {str(e)}", exc_info=True)
            raise ModelError(f"ONNX批量推理失败: {str(e)}")

    def _onnx_predict_single(
        self, image: np.ndarray, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ONNX单张图片推理"""
        try:
            # 预处理图像
            img = cv2.resize(image, (self.input_shape[2], self.input_shape[3]))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = img.astype(np.float32) / 255.0
            img = img.transpose(2, 0, 1)
            img = np.expand_dims(img, axis=0)

            # 推理
            outputs = self.session.run(self.output_names, {self.input_name: img})

            # 后处理结果
            if isinstance(outputs[0], np.ndarray) and len(outputs[0]) > 0:
                output = outputs[0][0]  # 假设第一个输出是检测结果
                boxes = output[:, :4]  # 边界框
                scores = output[:, 4]  # 置信度
                class_ids = output[:, 5]  # 类别ID

                # 应用NMS
                indices = cv2.dnn.NMSBoxes(
                    boxes.tolist(),
                    scores.tolist(),
                    params["conf"],
                    params["iou"],
                )

                # 构建结果
                result = {
                    "boxes": boxes[indices],
                    "scores": scores[indices],
                    "class_ids": class_ids[indices],
                }
                return result
            else:
                logger.warning("ONNX输出格式不符合预期")
                return {
                    "boxes": np.array([]),
                    "scores": np.array([]),
                    "class_ids": np.array([]),
                }

        except Exception as e:
            logger.error(f"ONNX单张图片推理失败: {str(e)}", exc_info=True)
            raise ModelError(f"ONNX单张图片推理失败: {str(e)}")

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
            if self.is_onnx:
                # 复制ONNX模型文件
                import shutil

                shutil.copy2(self.model_path, save_path)
            else:
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
            self.is_onnx = str(model_path).endswith(".onnx")
            if self.is_onnx:
                self._load_onnx_model()
            else:
                self._load_torch_model()
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
        info = {
            "model_path": str(self.model_path),
            "parameters": self.params,
            "format": "ONNX" if self.is_onnx else "PyTorch",
        }

        if self.is_onnx:
            info.update(
                {
                    "input_shape": self.input_shape,
                    "output_names": self.output_names,
                    "metadata": self.metadata,
                }
            )
        else:
            info.update(
                {
                    "device": self.model.device,
                    "task": self.model.task,
                }
            )

        return info


class DetectYOLOModel(BaseYOLOModel):
    """专注于目标检测任务的模型"""

    def __init__(
        self,
        model_path: Union[str, Path],
        params: Optional[Dict[str, Any]] = None,
        session_options: Optional[Any] = None,
    ):
        super().__init__(model_path, params, session_options)

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

    def _parse_detect_results(
        self, results: Union[List[Any], Any]
    ) -> List[Dict[str, Any]]:
        """
        解析推理结果，返回包含 bbox 对象的结果

        Args:
            results: YOLO 推理结果

        Returns:
            解析后的结果列表
        """
        parsed_results = []

        # 处理ONNX模型的结果（dict类型）
        if isinstance(results, dict):
            if "boxes" in results and len(results["boxes"]) > 0:
                boxes = results["boxes"]
                scores = results["scores"]
                class_ids = results["class_ids"]

                for i in range(len(boxes)):
                    box = boxes[i]
                    score = scores[i]
                    class_id = int(class_ids[i])

                    # 归一化置信度（如果大于1，则除以100）
                    confidence = float(score)
                    if confidence > 1:
                        confidence = confidence / 100.0

                    # 获取类别名称
                    if hasattr(self, "class_names") and self.class_names:
                        class_name = self.class_names.get(class_id, f"Class_{class_id}")
                    else:
                        class_name = f"Class_{class_id}"

                    result_item = {
                        "type": "detect",
                        "class_name": class_name,
                        "confidence": confidence,
                        "bbox": {
                            "x": int(box[0]),
                            "y": int(box[1]),
                            "width": int(box[2] - box[0]),
                            "height": int(box[3] - box[1]),
                        },
                        "class_id": class_id,
                        "area": int((box[2] - box[0]) * (box[3] - box[1])),
                    }
                    parsed_results.append(result_item)
            return parsed_results

        # 处理非ONNX模型的结果（list类型）
        if not isinstance(results, list):
            results = [results]

        for result in results:
            # 确保结果是可迭代的
            if hasattr(result, "boxes"):
                boxes = result.boxes
                names = result.names
                for box in boxes:
                    # 确保数据在CPU上并转换为Python类型
                    class_id = int(box.cls.cpu().numpy())
                    bbox_list = box.xyxy.cpu().numpy().squeeze().tolist()
                    bbox_list = [int(coord) for coord in bbox_list]

                    result_item = {
                        "type": "detect",
                        "class_name": names[class_id],
                        "confidence": float(box.conf.cpu().numpy().squeeze()),
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
        session_options: Optional[Any] = None,
    ):
        super().__init__(model_path, params, session_options)

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

    def _parse_classify_results(
        self, results: Union[List[Any], Any]
    ) -> List[Dict[str, Any]]:
        """
        解析推理结果

        Args:
            results: YOLO 推理结果

        Returns:
            解析后的结果列表
        """
        if not isinstance(results, list):
            results = [results]

        parsed_results = []
        for result in results:
            if hasattr(result, "probs"):
                # 确保数据在CPU上并转换为Python类型
                top1_index = int(result.probs.top1.cpu().numpy())
                top1_label = result.names[top1_index]
                top1_confidence = float(result.probs.top1conf.cpu().numpy())

                # 获取前5个最可能的类别
                top5_indices = result.probs.top5.cpu().numpy()
                top5_confidences = result.probs.top5conf.cpu().numpy().tolist()
                top5_labels = [result.names[i] for i in top5_indices]

                result_info = {
                    "type": "classify",
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
