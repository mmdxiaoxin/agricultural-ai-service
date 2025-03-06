# modules/task/routes.py
from flask import Blueprint
from .controller import (
    get_tasks_controller,
    get_task_controller,
    add_task_controller,
    update_task_controller,
    delete_task_controller,
)

task_bp = Blueprint("tasks", __name__)

task_bp.route("/tasks", methods=["GET"])(get_tasks_controller)
task_bp.route("/tasks/<int:task_id>", methods=["GET"])(get_task_controller)
task_bp.route("/tasks", methods=["POST"])(add_task_controller)
task_bp.route("/tasks/<int:task_id>", methods=["PUT"])(update_task_controller)
task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])(delete_task_controller)
