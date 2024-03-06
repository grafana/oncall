from django.db.models import Min

from apps.alerts.incident_appearance.templaters import TemplateLoader
from apps.alerts.tasks.task_logger import task_logger
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from common.jinja_templater import apply_jinja_template

# BATCH_SIZE is how many alert groups will be processed per second (for every individual alert receive channel)
BATCH_SIZE = 1000


def batch_ids(queryset, cursor):
    return list(queryset.filter(id__gt=cursor).order_by("id").values_list("id", flat=True)[:BATCH_SIZE])


@shared_dedicated_queue_retry_task
def update_web_title_cache_for_alert_receive_channel(alert_receive_channel_pk):
    """
    Update the web_title_cache field for all alert groups of alert receive channel with pk = alert_receive_channel_pk.
    Note that it's not invoked on web title template change due to performance considerations.
    """
    task_logger.debug(
        f"Starting update_web_title_cache_for_alert_receive_channel, alert_receive_channel_pk: {alert_receive_channel_pk}"
    )

    from apps.alerts.models import AlertGroup

    countdown = 0
    cursor = 0
    queryset = AlertGroup.objects.filter(channel_id=alert_receive_channel_pk)
    ids = batch_ids(queryset, cursor)

    while ids:
        update_web_title_cache.apply_async((alert_receive_channel_pk, ids), countdown=countdown)

        cursor = ids[-1]
        ids = batch_ids(queryset, cursor)
        countdown += 1


@shared_dedicated_queue_retry_task
def update_web_title_cache(alert_receive_channel_pk, alert_group_pks):
    """
    Update the web_title_cache field for alert groups with pk in alert_group_pks,
    for alert receive channel with pk = alert_receive_channel_pk.
    """
    task_logger.debug(
        f"Starting update_web_title_cache, alert_receive_channel_pk: {alert_receive_channel_pk}, "
        f"first alert_group_pk: {alert_group_pks[0]}, last alert_group_pk: {alert_group_pks[-1]}"
    )

    from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel

    try:
        alert_receive_channel = AlertReceiveChannel.objects_with_deleted.get(pk=alert_receive_channel_pk)
    except AlertReceiveChannel.DoesNotExist:
        task_logger.warning(f"AlertReceiveChannel {alert_receive_channel_pk} doesn't exist")
        return

    alert_groups = AlertGroup.objects.filter(pk__in=alert_group_pks).only("pk")

    # get first alerts in 2 SQL queries
    alerts_info = (
        Alert.objects.values("group_id").filter(group_id__in=alert_group_pks).annotate(first_alert_id=Min("id"))
    )
    alerts_info_map = {info["group_id"]: info for info in alerts_info}

    first_alert_ids = [info["first_alert_id"] for info in alerts_info_map.values()]
    first_alerts = Alert.objects.filter(pk__in=first_alert_ids).values("group_id", "raw_request_data")
    first_alert_map = {alert["group_id"]: alert for alert in first_alerts}

    template_manager = TemplateLoader()
    web_title_template = template_manager.get_attr_template("title", alert_receive_channel, render_for="web")

    for alert_group in alert_groups:
        if web_title_template:
            if alert_group.pk in first_alert_map:
                raw_request_data = first_alert_map[alert_group.pk]["raw_request_data"]
                web_title_cache = apply_jinja_template(web_title_template, raw_request_data)
            else:
                web_title_cache = None
        else:
            web_title_cache = None

        alert_group.web_title_cache = web_title_cache

    AlertGroup.objects.bulk_update(alert_groups, ["web_title_cache"])
