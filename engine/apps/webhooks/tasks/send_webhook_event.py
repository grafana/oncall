import logging
from json import JSONDecodeError

from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.utils import timezone

from apps.webhooks.models.webhooks import WebhookLog
from apps.webhooks.utils import InvalidWebhookData, InvalidWebhookHeaders, InvalidWebhookTrigger, InvalidWebhookUrl
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_webhook_event(trigger_type, data, user_id=None, team_id=None, org_id=None):
    Webhooks = apps.get_model("webhooks", "Webhook")
    webhooks_qs = Webhooks.objects.filter(trigger_type=trigger_type, organization_id=org_id)
    if user_id:
        webhooks_qs = webhooks_qs.filter(user_id=user_id)
    if team_id:
        webhooks_qs = webhooks_qs.filter(team_id=team_id)

    for webhook in webhooks_qs:
        execute_webhook.apply_async((webhook.pk, data))


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def execute_webhook(webhook_pk, data):
    Webhooks = apps.get_model("webhooks", "Webhook")

    status = {
        "last_run_at": timezone.now(),
        "input_data": data,
        "url": None,
        "trigger": None,
        "request": None,
        "response_status": None,
        "response": None,
    }

    try:
        webhook = Webhooks.objects.get(pk=webhook_pk)
        triggered, status["trigger"] = webhook.check_trigger(data)
        if triggered:
            status["url"] = webhook.build_url(data)
            request_kwargs = webhook.build_request_kwargs(data)
            if webhook.forward_all:
                status["request"] = "All input_data forwarded as payload"
            elif "json" in request_kwargs:
                status["request"] = request_kwargs["json"]
            else:
                status["request"] = request_kwargs.get("data")
            response = webhook.make_request(status["url"], request_kwargs)
            status["response_status"] = response.status_code
            try:
                status["response"] = response.json()
            except JSONDecodeError:
                status["response"] = response.content.decode("utf-8")
    except Webhooks.DoesNotExist:
        logger.warn(f"Webhook {webhook_pk} does not exist")
        return
    except InvalidWebhookUrl as e:
        status["url"] = e.message
    except InvalidWebhookTrigger as e:
        status["trigger"] = e.message
    except (InvalidWebhookHeaders, InvalidWebhookData) as e:
        status["request"] = e.message
    except Exception as e:
        status["response"] = str(e)
    finally:
        WebhookLog.objects.update_or_create(webhook_id=webhook_pk, defaults=status)
