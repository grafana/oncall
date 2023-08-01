from django.conf import settings
from django.db import transaction
from django.db.models import ExpressionWrapper, F, fields
from django.utils import timezone

from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.insight_log import MaintenanceEvent, write_maintenance_insight_log

from .task_logger import task_logger


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def disable_maintenance(*args, **kwargs):
    from apps.alerts.models import AlertGroup
    from apps.user_management.models import User

    user = None
    object_under_maintenance = None
    user_id = kwargs.get("user_id")
    if user_id:
        user = User.objects.get(pk=user_id)

    force = kwargs.get("force", False)
    with transaction.atomic():
        if "alert_receive_channel_id" in kwargs:
            from apps.alerts.models import AlertReceiveChannel

            alert_receive_channel_id = kwargs["alert_receive_channel_id"]
            try:
                object_under_maintenance = AlertReceiveChannel.objects.select_for_update().get(
                    pk=alert_receive_channel_id,
                )
            except AlertReceiveChannel.DoesNotExist:
                task_logger.info(
                    f"AlertReceiveChannel for disable_maintenance does not exists. Id: {alert_receive_channel_id}"
                )

        else:
            task_logger.info(f"Invalid instance id passed in disable_maintenance. Got: {kwargs}")

        if object_under_maintenance is not None and (
            disable_maintenance.request.id == object_under_maintenance.maintenance_uuid or force
        ):
            organization = object_under_maintenance.get_organization()
            write_maintenance_insight_log(object_under_maintenance, user, MaintenanceEvent.FINISHED)
            if object_under_maintenance.maintenance_mode == object_under_maintenance.MAINTENANCE:
                mode_verbal = "Maintenance"
                maintenance_incident = AlertGroup.objects.get(
                    maintenance_uuid=object_under_maintenance.maintenance_uuid
                )
                transaction.on_commit(maintenance_incident.resolve_by_disable_maintenance)
            if object_under_maintenance.maintenance_mode == object_under_maintenance.DEBUG_MAINTENANCE:
                mode_verbal = "Debug"
            # Use mode_verbal variable instead of object_under_maintenance.get_maintenance_mode_display()
            # because after transaction maintenance_mode is None.
            if organization.slack_team_identity:
                transaction.on_commit(
                    lambda: object_under_maintenance.notify_about_maintenance_action(
                        f"{mode_verbal} of {object_under_maintenance.get_verbal()} finished."
                    )
                )

            object_under_maintenance.maintenance_uuid = None
            object_under_maintenance.maintenance_duration = None
            object_under_maintenance.maintenance_mode = None
            object_under_maintenance.maintenance_started_at = None
            object_under_maintenance.maintenance_author = None
            object_under_maintenance.save(
                update_fields=[
                    "maintenance_uuid",
                    "maintenance_duration",
                    "maintenance_mode",
                    "maintenance_started_at",
                    "maintenance_author",
                ]
            )


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def check_maintenance_finished(*args, **kwargs):
    from apps.alerts.models import AlertReceiveChannel

    now = timezone.now()
    maintenance_finish_at = ExpressionWrapper(
        (F("maintenance_started_at") + F("maintenance_duration")), output_field=fields.DateTimeField()
    )
    alert_receive_channel_with_expired_maintenance_ids = (
        AlertReceiveChannel.objects.filter(maintenance_started_at__isnull=False)
        .annotate(maintenance_finish_at=maintenance_finish_at)
        .filter(maintenance_finish_at__lt=now)
        .values_list("pk", flat=True)
    )

    for id in alert_receive_channel_with_expired_maintenance_ids:
        disable_maintenance.apply_async(
            args=(),
            kwargs={"alert_receive_channel_id": id, "force": True},
        )
