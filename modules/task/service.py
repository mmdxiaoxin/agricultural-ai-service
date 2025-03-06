# modules/task/service.py
from .task import get_all_tasks, get_task_by_id, create_task, update_task, delete_task


def get_tasks():
    return get_all_tasks()


def get_task(task_id):
    return get_task_by_id(task_id)


def add_task(title):
    return create_task(title)


def update_task(task_id, title, done):
    return update_task(task_id, title, done)


def delete_task(task_id):
    return delete_task(task_id)
