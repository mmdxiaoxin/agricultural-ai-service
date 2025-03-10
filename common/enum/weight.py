# common/enum/weight.py

import os
from enum import Enum


class ModelWeights(Enum):
    YOLO11_BEST = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../weight/yolo11/classify-best.pt")
    )
    YOLO11_LAST = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../weight/yolo11/classify-last.pt")
    )
