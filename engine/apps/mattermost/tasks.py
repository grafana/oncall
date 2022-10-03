from django.apps import apps
from django.conf import settings

from apps.mattermost.alert_rendering import build_log_message, get_templated_fields
from apps.mattermost.backend import BACKEND_ID
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


def check_backend_enabled(alert_group):
    channel_info = None
    if alert_group.channel_filter and alert_group.channel_filter.notification_backends is not None:
        channel_info = alert_group.channel_filter.notification_backends.get(BACKEND_ID)

    if channel_info is None or not channel_info.get("enabled"):
        return False, None

    return True, channel_info.get("channel")


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def notify_user_async(self, alert_group_pk, user_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)
    # TODO: get backend user information
    User = apps.get_model("user_management", "User")
    user = User.objects.get(pk=user_pk)

    # TODO: if there is a channel message for this alert group, ping the user there
    # otherwise, send a DM with the alert details

    title, message = get_templated_fields(alert_group)
    # mention user
    message += f"\n Inviting *{user.username}* to look at the incident"

    # TODO: send user notification
    # (channel or DM, using mattermost interactive messages; track messages for pushing status updates)
    print(title)
    print(message)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_create_alert_async(self, alert_pk):
    Alert = apps.get_model("alerts", "Alert")
    alert = Alert.objects.get(pk=alert_pk)
    alert_group = alert.group

    # potentially get channel filter information indicating where to post the alert message
    # check backend enabled
    enabled, channel = check_backend_enabled(alert_group)
    if not enabled:
        return

    # TODO: post to expected channel
    # (using mattermost interactive messages; track messages for pushing status updates)
    title, message = get_templated_fields(alert_group)
    print(title)
    print(message)

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

    # TODO: rebuild message and update existing alert messages (if there are)
    title, message = get_templated_fields(alert_group)
    print(title)
    print(message)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def post_alert_logs_async(self, alert_group_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)

    enabled, channel = check_backend_enabled(alert_group)
    if not enabled:
        return

    # TODO: get previous alert group sent message, reply to it
    # build log message and send as a reply to the alert messages (if there are)
    title, message = build_log_message(alert_group)
    print(title)
    print(message)


@shared_dedicated_queue_retry_task(
    bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_update_log_record_async(self, alert_group_pk):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)

    enabled, channel = check_backend_enabled(alert_group)
    if not enabled:
        return

    # rebuild log message and update existing log messages
    title, message = build_log_message(alert_group)
    print(title)
    print(message)
