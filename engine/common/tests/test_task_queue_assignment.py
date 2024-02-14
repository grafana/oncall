from celery import current_app

from settings.celery_task_routes import CELERY_TASK_ROUTES

"""
If a task has a legitimate reason to not have a queue assignment it can
be added here (In development, in process of deprecation, etc.) if possible
we should avoid @shared_dedicated_queue_retry_task or @shared_task and
remove entirely if it is not needed.
"""
COMMON_IGNORED_TASKS = {
    "common.custom_celery_tasks.tests.test_dedicated_queue_retry_task.my_task",
    "common.custom_celery_tasks.tests.test_log_exception_on_failure_task.my_task",
    "common.custom_celery_tasks.tests.test_log_exception_on_failure_task.my_task_two",
}


def check_celery_task_route_mapping(task_ids, ignored_prefixes, additional_ignored_tasks=None):
    tasks = set(k for k in current_app.tasks.keys() if not k.startswith(ignored_prefixes))
    tasks -= set(COMMON_IGNORED_TASKS)
    if additional_ignored_tasks:
        tasks -= set(additional_ignored_tasks)
    tasks -= set(task_ids)
    if tasks:
        print(f"Unassigned queue for celery task {tasks}")
    assert len(tasks) == 0


def test_celery_task_route_mapping():
    """
    If this test does not pass make sure you have added any newly added
    @shared_dedicated_queue_retry_task or @shared_task to CELERY_TASK_ROUTES
    in engine/settings/celery_task_routes.py
    """
    check_celery_task_route_mapping(CELERY_TASK_ROUTES.keys(), ("extensions", "celery"))
