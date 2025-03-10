from flask import Blueprint
from .controller import plant_detect_controller

yolo8_bp = Blueprint("yolo8", __name__)

yolo8_bp.route("/yolo8/plant/detect", methods=["POST"])(plant_detect_controller)
