import io
from typing import Any

from PIL import Image
from common.utils.exceptions import ModelError
from common.utils.logger import log_manager

# 获取日志记录器
logger = log_manager.get_logger(__name__)


class ImageProcessor:
    """图片处理工具类"""

    @staticmethod
    def preprocess(image_data: bytes) -> Any:
        """
        预处理图片数据

        Args:
            image_data: 图片二进制数据

        Returns:
            处理后的图片数据
        """
        try:
            logger.info("开始图片预处理...")
            logger.info(f"输入数据大小: {len(image_data)} 字节")

            # 将二进制数据转换为图片
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"图片大小: {image.size}, 模式: {image.mode}")

            # 转换为RGB模式
            if image.mode != "RGB":
                logger.info("转换图片为RGB模式")
                image = image.convert("RGB")

            # 调整图片大小
            if image.size != (640, 640):
                logger.info("调整图片大小为 640x640")
                image = image.resize((640, 640), Image.Resampling.LANCZOS)

            logger.info("图片预处理完成")
            return image

        except Exception as e:
            logger.error(f"图片预处理失败: {str(e)}", exc_info=True)
            raise ModelError(f"图片预处理失败: {str(e)}")
