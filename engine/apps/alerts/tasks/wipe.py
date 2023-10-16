from django.conf import settings

from common.custom_celery_tasks import shared_dedicated_queue_retry_task


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def wipe(alert_group_pk, user_pk):
    from apps.alerts.models import AlertGroup
    from apps.api.serializers.alert import AlertFieldsCacheSerializerMixin
    from apps.api.serializers.alert_group import AlertGroupFieldsCacheSerializerMixin
    from apps.user_management.models import User

    alert_group = AlertGroup.objects.filter(pk=alert_group_pk).first()
    user = User.objects.filter(pk=user_pk).first()
    alert_group.wipe_by_user(user)

    # Clear internal API cache
    AlertGroupFieldsCacheSerializerMixin.bust_object_caches(alert_group)
    for alert in alert_group.alerts.all():
        AlertFieldsCacheSerializerMixin.bust_object_caches(alert)
