import io

from PIL import Image


class ImageProcessor:
    """图片处理工具类"""

    @staticmethod
    def preprocess(image_data):
        """
        预处理输入图像数据
        :param image_data: 输入的图像数据（bytes类型）
        :return: 处理后的 PIL 图像
        """
        return Image.open(io.BytesIO(image_data))
