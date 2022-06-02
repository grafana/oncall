from django.apps import apps
from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def wipe(alert_group_pk, user_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    User = apps.get_model("user_management", "User")
    alert_group = AlertGroup.all_objects.filter(pk=alert_group_pk).first()
    user = User.objects.filter(pk=user_pk).first()
    alert_group.wipe_by_user(user)
