import os

from django.apps import apps
from django.conf import settings
from plyer import notification

from apps.dnotify.alert_rendering import build_log_message, get_templated_fields
from apps.dnotify.backend import BACKEND_ID
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


def trigger_notification(title, message):
    icon_path = os.path.join(settings.BASE_DIR, "apps/dnotify/logo.ico")
    notification.notify(
        title=title,
        message=message,
        app_name="Grafana OnCall",
        app_icon=icon_path,
        timeout=10,
    )


def check_backend_enabled(alert_group):
    channel_info = None
    if alert_group.channel_filter and alert_group.channel_filter.notification_backends is not None:
        channel_info = alert_group.channel_filter.notification_backends.get(BACKEND_ID)

    if channel_info is None or not channel_info.get("enabled"):
        return False, None

    return True, channel_info.get("channel", "no-channel")


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def notify_user_async(self, alert_group_pk, user_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)
    # get backend user information
    User = apps.get_model("user_management", "User")
    user = User.objects.get(pk=user_pk)

    title, message = get_templated_fields(alert_group)
    # mention user
    message += f"\n Inviting *{user.username}* to look at the incident"

    trigger_notification(title, message)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_create_alert_async(self, alert_pk):
    Alert = apps.get_model("alerts", "Alert")
    alert = Alert.objects.get(pk=alert_pk)
    alert_group = alert.group

    # potentially get channel filter information indicating where to post the alert message
    # check backend enabled; filter: all, only mine?
    enabled, channel = check_backend_enabled(alert_group)
    if not enabled:
        return

    # build message and send; keep track of the message to add updates as replies
    title, message = get_templated_fields(alert_group)
    message += f"\nChannel: {channel}"
    trigger_notification(title, message)

    post_alert_logs_async.apply_async((alert_group.pk,))


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_update_alert_async(self, alert_group_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)

    enabled, channel = check_backend_enabled(alert_group)
    if not enabled:
        return

    # rebuild message and update existing alert messages (if there are)
    title, message = get_templated_fields(alert_group)
    trigger_notification(title, message)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def post_alert_logs_async(self, alert_group_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)

    enabled, channel = check_backend_enabled(alert_group)
    if not enabled:
        return

    # get previous sent message, reply to it
    # build message and send as a reply to the alert messages (if there are)
    title, message = build_log_message(alert_group)
    trigger_notification(title, message)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_update_log_record_async(self, alert_group_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)

    enabled, channel = check_backend_enabled(alert_group)
    if not enabled:
        return

    # rebuild message and update existing log messages
    title, message = build_log_message(alert_group)
    trigger_notification(title, message)
