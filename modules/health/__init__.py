from flask import Blueprint

health_bp = Blueprint("health", __name__)

from . import routes
