from django.apps import apps

from apps.alerts.utils import render_curl_command, request_outgoing_webhook
from apps.slack.slack_client import SlackClientWithErrorHandling
from common.custom_celery_tasks import shared_dedicated_queue_retry_task


# TODO: this appears to be not used anymore. there is no traffic on this task
# this task + the code path that creates these tasks, can likely be removed
@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def call_ack_url(ack_url, alert_group_pk, channel, http_method="GET"):
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    SlackMessage = apps.get_model("slack", "SlackMessage")
    alert_group = AlertGroup.all_objects.filter(pk=alert_group_pk)[0]
    is_successful, result_message = request_outgoing_webhook(ack_url, http_method)

    if is_successful:
        alert_group.acknowledged_on_source = True
        alert_group.save()
        debug_message = ""
        info_message = "OnCall successfully sent {} request to acknowledge alert on the source".format(http_method)
    else:
        curl_request = render_curl_command(ack_url, http_method)
        debug_message = "```{}```".format(curl_request)
        info_message = "OnCall attempted to acknowledge alert on the source with the result: `{}`".format(
            result_message
        )

    sc = (
        SlackClientWithErrorHandling(alert_group.channel.organization.slack_team_identity.bot_access_token)
        if channel is not None
        else None
    )

    text = "{}".format(debug_message)
    footer = "{}".format(info_message)
    blocks = [
        {
            "type": "section",
            "block_id": "alert",
            "text": {
                "type": "mrkdwn",
                "text": text,
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "block_id": "alert",
            "text": {
                "type": "mrkdwn",
                "text": footer,
            },
        },
    ]

    if channel is not None:
        result = sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=text,
            blocks=blocks,
            thread_ts=alert_group.slack_message.slack_id,
            mrkdwn=True,
        )
        SlackMessage(
            slack_id=result["ts"],
            organization=alert_group.channel.organization,
            _slack_team_identity=alert_group.channel.organization.slack_team_identity,
            channel_id=channel,
            alert_group=alert_group,
        ).save()
