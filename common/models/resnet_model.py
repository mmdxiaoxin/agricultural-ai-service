from typing import Dict, List, Optional, Union, Any
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from pathlib import Path
import io
from PIL import Image
import onnxruntime as ort

from config.resnet_config import ResNetConfig
from common.utils.exceptions import ModelError
from common.utils.logger import log_manager

logger = log_manager.get_logger(__name__)


class ResNetModel:
    """通用的ResNet模型类，支持不同版本的ResNet模型和ONNX格式"""

    def __init__(
        self,
        model_path: Union[str, Path],
        version: str = "resnet18",
        params: Optional[Dict[str, Any]] = None,
        session_options: Optional[Any] = None,
    ):
        """
        初始化ResNet模型

        Args:
            model_path: 模型路径
            version: ResNet版本，支持: resnet18, resnet34, resnet50, resnet101, resnet152
            params: 初始化参数
            session_options: ONNX Runtime会话选项

        Raises:
            ModelError: 当模型加载失败时抛出
        """
        try:
            logger.info(f"开始初始化ResNet模型，版本: {version}，路径: {model_path}")

            # 验证模型版本
            if version not in ResNetConfig.SUPPORTED_VERSIONS:
                raise ValueError(f"不支持的ResNet版本: {version}")

            self.model_path = Path(model_path)
            if not self.model_path.exists():
                raise FileNotFoundError(f"模型文件不存在: {model_path}")

            # 获取默认配置并更新
            self.params = ResNetConfig.get_default_config(version)
            if params:
                self.params.update(params)

            # 保存会话选项
            self.session_options = session_options

            # 设置设备
            self.device = torch.device(
                self.params["device"] if torch.cuda.is_available() else "cpu"
            )
            logger.info(f"使用设备: {self.device}")

            # 判断模型格式并加载
            self.is_onnx = str(self.model_path).endswith(".onnx")
            if self.is_onnx:
                self._load_onnx_model()
            else:
                self._load_torch_model(version)

            # 设置图像预处理
            self._setup_transforms()

            logger.info(
                f"成功加载ResNet模型: {version} ({'ONNX' if self.is_onnx else 'PyTorch'})"
            )

        except Exception as e:
            logger.error(f"ResNet模型加载失败: {str(e)}", exc_info=True)
            raise ModelError(f"ResNet模型加载失败: {str(e)}")

    def _load_onnx_model(self):
        """加载ONNX模型"""
        try:
            # 创建ONNX运行时会话
            providers = (
                ["CUDAExecutionProvider", "CPUExecutionProvider"]
                if torch.cuda.is_available()
                else ["CPUExecutionProvider"]
            )
            self.session = ort.InferenceSession(
                str(self.model_path),
                providers=providers,
                sess_options=self.session_options,
            )

            # 获取输入输出信息
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name

            # 获取输入形状
            self.input_shape = self.session.get_inputs()[0].shape
            logger.info(f"ONNX模型输入形状: {self.input_shape}")

            # 获取类别数量
            self.num_classes = self.session.get_outputs()[0].shape[1]
            logger.info(f"ONNX模型类别数量: {self.num_classes}")

        except Exception as e:
            logger.error(f"ONNX模型加载失败: {str(e)}", exc_info=True)
            raise ModelError(f"ONNX模型加载失败: {str(e)}")

    def _load_torch_model(self, version: str):
        """加载PyTorch模型"""
        try:
            logger.info("开始加载PyTorch模型...")

            # 检查CUDA可用性并记录
            cuda_available = torch.cuda.is_available()
            if cuda_available:
                logger.info(f"CUDA可用，使用GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("CUDA不可用，将使用CPU进行推理")

            # 加载模型权重，优先使用GPU，如果失败则回退到CPU
            try:
                checkpoint = torch.load(str(self.model_path), map_location=self.device)
            except Exception as e:
                logger.warning(f"使用指定设备加载模型失败: {str(e)}，尝试使用CPU加载")
                checkpoint = torch.load(str(self.model_path), map_location="cpu")
                # 如果原本指定的是GPU但加载失败，更新设备为CPU
                if self.device.type != "cpu":
                    self.device = torch.device("cpu")
                    logger.info("已切换到CPU设备")

            # 获取类别数量
            num_classes = checkpoint["model_state_dict"]["fc.weight"].size(0)
            logger.info(f"模型类别数量: {num_classes}")

            # 创建模型实例
            model_class = ResNetConfig.get_model_class(version)
            self.model = model_class(weights=None)

            # 修改最后的全连接层
            self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)

            # 加载模型权重
            try:
                self.model.load_state_dict(checkpoint["model_state_dict"])
            except Exception as e:
                logger.error(f"加载模型权重失败: {str(e)}")
                raise ModelError(f"加载模型权重失败: {str(e)}")

            # 设置为评估模式
            self.model.eval()

            # 移动到指定设备
            try:
                self.model = self.model.to(self.device)
                logger.info(f"模型已移动到设备: {self.device}")
            except Exception as e:
                logger.warning(f"移动模型到指定设备失败: {str(e)}，尝试使用CPU")
                self.device = torch.device("cpu")
                self.model = self.model.to(self.device)
                logger.info("模型已移动到CPU设备")

            # 如果使用半精度且设备不是CPU
            if self.params.get("half", False) and self.device.type != "cpu":
                try:
                    self.model = self.model.half()
                    logger.info("已启用半精度推理")
                except Exception as e:
                    logger.warning(f"启用半精度失败: {str(e)}，将使用全精度")
                    self.params["half"] = False

            # 获取类别映射
            self.classes = checkpoint.get("classes", None)
            if self.classes:
                logger.info(f"加载类别映射，共 {len(self.classes)} 个类别")

        except Exception as e:
            logger.error(f"PyTorch模型加载失败: {str(e)}", exc_info=True)
            raise ModelError(f"PyTorch模型加载失败: {str(e)}")

    def _setup_transforms(self):
        """设置图像预处理"""
        self.transform = transforms.Compose(
            [
                transforms.Resize((self.params["img_size"], self.params["img_size"])),
                transforms.ToTensor(),
                transforms.Normalize(mean=self.params["mean"], std=self.params["std"]),
            ]
        )

    def _process_batch(
        self, batch: List[bytes], params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """处理批量图片"""
        batch_tensors = []
        for img_bytes in batch:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_tensor = self.transform(img)
            batch_tensors.append(img_tensor)

        # 堆叠为批次
        input_batch = torch.stack(batch_tensors)

        if self.is_onnx:
            # ONNX推理
            input_batch = input_batch.numpy()
            outputs = self.session.run(
                [self.output_name], {self.input_name: input_batch}
            )[0]
            probabilities = torch.nn.functional.softmax(
                torch.from_numpy(outputs), dim=1
            )
        else:
            # PyTorch推理
            input_batch = input_batch.to(self.device)
            if params.get("half", False) and self.device.type != "cpu":
                input_batch = input_batch.half()
            with torch.no_grad():
                outputs = self.model(input_batch)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)

        predicted_probs, predicted_classes = torch.max(probabilities, 1)
        top5_probs, top5_indices = torch.topk(probabilities, 5, dim=1)

        # 处理每张图片的结果
        results = []
        for i, (prob, class_idx) in enumerate(zip(predicted_probs, predicted_classes)):
            class_idx = class_idx.item()
            prob = prob.item()

            # 获取类别名称
            if hasattr(self, "classes") and self.classes:
                class_name = self.classes[class_idx]
            else:
                class_name = f"Class_{class_idx}"

            # 获取top5预测结果
            top5_results = []
            for j in range(5):
                top5_class_idx = top5_indices[i][j].item()
                top5_prob = top5_probs[i][j].item()
                if hasattr(self, "classes") and self.classes:
                    top5_class_name = self.classes[top5_class_idx]
                else:
                    top5_class_name = f"Class_{top5_class_idx}"
                top5_results.append(
                    {
                        "class_id": top5_class_idx,
                        "class_name": top5_class_name,
                        "confidence": top5_prob,
                    }
                )

            result = {
                "class_id": class_idx,
                "class_name": class_name,
                "confidence": prob,
                "type": "classify",
                "top5": top5_results,
            }
            results.append(result)

        return results

    def _process_single(
        self, image_data: bytes, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理单张图片"""
        img = Image.open(io.BytesIO(image_data)).convert("RGB")
        img_tensor = self.transform(img)
        if not isinstance(img_tensor, torch.Tensor):
            img_tensor = torch.from_numpy(img_tensor)
        img_tensor = img_tensor.unsqueeze(0)

        if self.is_onnx:
            # ONNX推理
            img_tensor = img_tensor.numpy()
            outputs = self.session.run(
                [self.output_name], {self.input_name: img_tensor}
            )[0]
            probabilities = torch.nn.functional.softmax(
                torch.from_numpy(outputs), dim=1
            )
        else:
            # PyTorch推理
            img_tensor = img_tensor.to(self.device)
            if params.get("half", False) and self.device.type != "cpu":
                img_tensor = img_tensor.half()
            with torch.no_grad():
                outputs = self.model(img_tensor)
                probabilities = torch.nn.functional.softmax(outputs, dim=1)

        predicted_prob, predicted_class = torch.max(probabilities, 1)
        top5_probs, top5_indices = torch.topk(probabilities, 5, dim=1)

        # 获取预测结果
        class_idx = predicted_class.item()
        prob = predicted_prob.item()

        # 获取类别名称
        if hasattr(self, "classes") and self.classes:
            class_name = self.classes[class_idx]
        else:
            class_name = f"Class_{class_idx}"

        # 获取top5预测结果
        top5_results = []
        for i in range(5):
            top5_class_idx = top5_indices[0][i].item()
            top5_prob = top5_probs[0][i].item()
            if hasattr(self, "classes") and self.classes:
                top5_class_name = self.classes[top5_class_idx]
            else:
                top5_class_name = f"Class_{top5_class_idx}"
            top5_results.append(
                {
                    "class_id": top5_class_idx,
                    "class_name": top5_class_name,
                    "confidence": top5_prob,
                }
            )

        return {
            "class_id": class_idx,
            "class_name": class_name,
            "confidence": prob,
            "type": "classify",
            "top5": top5_results,
        }

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
            推理结果列表

        Raises:
            ModelError: 当推理过程出错时抛出
        """
        try:
            logger.info("开始ResNet模型推理...")

            # 合并默认参数和传入的参数
            predict_params = self.params.copy()
            predict_params.update(kwargs)

            results = []
            # 处理单张或多张图片
            if isinstance(image_data, list):
                # 批量处理
                logger.info(f"批量处理 {len(image_data)} 张图片...")
                for i in range(0, len(image_data), batch_size):
                    batch = image_data[i : i + batch_size]
                    batch_results = self._process_batch(batch, predict_params)
                    results.extend(batch_results)
            else:
                # 单张图片处理
                logger.info("处理单张图片...")
                result = self._process_single(image_data, predict_params)
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
            分类结果列表
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
            "version": self.params.get("version", "resnet18"),
            "num_classes": (
                len(self.classes) if hasattr(self, "classes") and self.classes else None
            ),
            "device": str(self.device),
            "format": "ONNX" if self.is_onnx else "PyTorch",
        }
