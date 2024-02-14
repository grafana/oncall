
from django.conf import settings
from django.db import transaction

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .task_logger import task_logger
from .notify_user import notify_user_task

@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def notify_team_members_task(
    team_pk,
    alert_group_pk,
    **kwargs # kwargs to pass through to notify_user_task.apply_async
):
    from apps.user_management.models import Team


    try:
        team = Team.objects.filter(pk=team_pk).first()
    except Team.DoesNotExist:
        return f"notify_team_members_task: team {team_pk} doesn't exist"


    for user in team.users.all():
        try:
            if user.is_notification_allowed:
                task_logger.debug(f"notify_team_members_task: notifying {user.pk}")
                notify_user_task.apply_async(
                    args=(
                        user.pk,
                        alert_group_pk,
                    ),
                    kwargs=kwargs
                )
        except:
                task_logger.info(f"notify_team_members_task: user {user.pk} failed")
