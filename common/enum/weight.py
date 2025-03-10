# common/enum/weight.py

import os
from enum import Enum


class ModelWeights(Enum):
    YOLO8_DETECT = None
    YOLO5_DETECT = None
    YOLO11_CLASSIFY = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../weight/yolo11/classify-best.pt")
    )
