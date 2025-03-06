# modules/task/task.py
tasks = [
    {"id": 1, "title": "Learn Flask", "done": False},
    {"id": 2, "title": "Build a REST API", "done": False},
]


def get_all_tasks():
    return tasks


def get_task_by_id(task_id):
    return next((task for task in tasks if task["id"] == task_id), None)


def create_task(title):
    new_task = {
        "id": tasks[-1]["id"] + 1 if tasks else 1,
        "title": title,
        "done": False,
    }
    tasks.append(new_task)
    return new_task


def update_task(task_id, title, done):
    task = get_task_by_id(task_id)
    if task:
        task["title"] = title
        task["done"] = done
    return task


def delete_task(task_id):
    task = get_task_by_id(task_id)
    if task:
        tasks.remove(task)
    return task
