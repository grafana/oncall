from celery import current_app

from settings.celery_task_routes import CELERY_TASK_ROUTES

"""
If a task has a legitimate reason to not have a queue assignment it can
be added here (In development, in process of deprecation, etc.) if possible
we should avoid the @shared_dedicated_queue_retry_task or @shared_task or
remove entirely if it is not needed.
"""
IGNORED_TASKS = [
    "apps.mobile_app.tasks.new_alert_group.notify_user_async",
    "apps.alerts.tasks.create_contact_points_for_datasource.schedule_create_contact_points_for_datasource",
    "common.oncall_gateway.tasks.create_slack_connector_async_v2",
]


def check_celery_task_route_mapping(task_ids, ignored_tasks=None):
    tasks = set(k for k in current_app.tasks.keys() if not k.startswith("celery"))
    if ignored_tasks:
        tasks -= set(ignored_tasks)
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
    check_celery_task_route_mapping(CELERY_TASK_ROUTES.keys(), IGNORED_TASKS)
