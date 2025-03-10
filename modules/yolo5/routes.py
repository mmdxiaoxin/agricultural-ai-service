from flask import Blueprint

from .controller import plant_detect_controller

yolo5_bp = Blueprint("yolo5", __name__)

yolo5_bp.route("/yolo5/plant/detect", methods=["POST"])(plant_detect_controller)
