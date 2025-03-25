class ModelError(Exception):
    """模型相关的异常基类"""

    pass


class ModelLoadError(ModelError):
    """模型加载失败异常"""

    pass


class ModelInferenceError(ModelError):
    """模型推理失败异常"""

    pass


class ModelSaveError(ModelError):
    """模型保存失败异常"""

    pass


class ModelParamError(ModelError):
    """模型参数错误异常"""

    pass


class ImageProcessError(Exception):
    """图像处理相关的异常"""

    pass
