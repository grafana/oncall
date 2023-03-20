import json
import logging
from json import JSONDecodeError

from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.utils import timezone

from apps.alerts.models import AlertGroup
from apps.user_management.models import User
from apps.webhooks.models import Webhook, WebhookLog
from apps.webhooks.utils import (
    InvalidWebhookData,
    InvalidWebhookHeaders,
    InvalidWebhookTrigger,
    InvalidWebhookUrl,
    serialize_event,
)
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_webhook_event(trigger_type, alert_group_id, team_id=None, organization_id=None, user_id=None):
    Webhooks = apps.get_model("webhooks", "Webhook")
    webhooks_qs = Webhooks.objects.filter(trigger_type=trigger_type, organization_id=organization_id, team_id=team_id)

    for webhook in webhooks_qs:
        execute_webhook.apply_async((webhook.pk, alert_group_id, user_id))


def _isoformat_date(date_value):
    return date_value.isoformat() if date_value else None


def _build_payload(trigger_type, alert_group_id, user_id):
    user = None
    try:
        alert_group = AlertGroup.unarchived_objects.get(pk=alert_group_id)
        if user_id is not None:
            user = User.objects.filter(pk=user_id).first()
    except AlertGroup.DoesNotExist:
        return

    if trigger_type == Webhook.TRIGGER_NEW:
        event = {
            "type": "Firing",
            "time": _isoformat_date(alert_group.started_at),
        }
    elif trigger_type == Webhook.TRIGGER_ACKNOWLEDGE:
        event = {
            "type": "Acknowledge",
            "time": _isoformat_date(alert_group.acknowledged_at),
        }
    elif trigger_type == Webhook.TRIGGER_RESOLVE:
        event = {
            "type": "Resolve",
            "time": _isoformat_date(alert_group.resolved_at),
        }
    elif trigger_type == Webhook.TRIGGER_SILENCE:
        event = {
            "type": "Silence",
            "time": _isoformat_date(alert_group.silenced_at),
            "until": _isoformat_date(alert_group.silenced_until),
        }
    elif trigger_type == Webhook.TRIGGER_UNSILENCE:
        event = {
            "type": "Unsilence",
        }
    elif trigger_type == Webhook.TRIGGER_UNRESOLVE:
        event = {
            "type": "Unresolve",
        }
    data = serialize_event(event, alert_group, user)
    return data


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def execute_webhook(webhook_pk, alert_group_id, user_id):
    Webhooks = apps.get_model("webhooks", "Webhook")
    try:
        webhook = Webhooks.objects.get(pk=webhook_pk)
    except Webhooks.DoesNotExist:
        logger.warn(f"Webhook {webhook_pk} does not exist")
        return

    data = _build_payload(webhook.trigger_type, alert_group_id, user_id)
    status = {
        "last_run_at": timezone.now(),
        "input_data": data,
        "url": None,
        "trigger": None,
        "headers": None,
        "data": None,
        "response_status": None,
        "response": None,
    }

    exception = None
    try:
        triggered, status["trigger"] = webhook.check_trigger(data)
        if triggered:
            status["url"] = webhook.build_url(data)
            request_kwargs = webhook.build_request_kwargs(data, raise_data_errors=True)
            status["headers"] = json.dumps(request_kwargs.get("headers", {}))
            if webhook.forward_all:
                status["data"] = "All input_data forwarded as payload"
            elif "json" in request_kwargs:
                status["data"] = json.dumps(request_kwargs["json"])
            else:
                status["data"] = request_kwargs.get("data")
            response = webhook.make_request(status["url"], request_kwargs)
            status["response_status"] = response.status_code
            try:
                status["response"] = json.dumps(response.json())
            except JSONDecodeError:
                status["response"] = response.content.decode("utf-8")
        else:
            # do not add a log entry if the webhook is not triggered
            return
    except InvalidWebhookUrl as e:
        status["url"] = e.message
    except InvalidWebhookTrigger as e:
        status["trigger"] = e.message
    except InvalidWebhookHeaders as e:
        status["headers"] = e.message
    except InvalidWebhookData as e:
        status["data"] = e.message
    except Exception as e:
        status["response"] = str(e)
        exception = e

    # create/update log entry
    WebhookLog.objects.update_or_create(webhook_id=webhook_pk, defaults=status)

    if exception:
        raise exception
