# modules/task/controller.py
from flask import jsonify, request
from .service import get_tasks, get_task, add_task, update_task, delete_task


def get_tasks_controller():
    tasks = get_tasks()
    return jsonify({"tasks": tasks})


def get_task_controller(task_id):
    task = get_task(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"task": task})


def add_task_controller():
    data = request.get_json()
    title = data.get("title")
    if not title:
        return jsonify({"error": "Title is required"}), 400
    task = add_task(title)
    return jsonify({"task": task}), 201


def update_task_controller(task_id):
    data = request.get_json()
    title = data.get("title")
    done = data.get("done")
    if not title:
        return jsonify({"error": "Title is required"}), 400
    task = update_task(task_id, title, done)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"task": task})


def delete_task_controller(task_id):
    task = delete_task(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task deleted"}), 200
