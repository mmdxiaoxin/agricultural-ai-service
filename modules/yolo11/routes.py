from flask import Blueprint
from .controller import plant_classify_controller

yolo11_bp = Blueprint("yolo11", __name__)

yolo11_bp.route("/yolo11/plant/classify", methods=["POST"])(plant_classify_controller)
