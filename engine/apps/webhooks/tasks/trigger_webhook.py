import json
import logging
import typing
from datetime import datetime
from json import JSONDecodeError

import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Prefetch

from apps.alerts.models import AlertGroup, AlertGroupLogRecord, EscalationPolicy
from apps.base.models import UserNotificationPolicyLogRecord
from apps.user_management.models import User
from apps.webhooks.models import Webhook, WebhookResponse
from apps.webhooks.models.webhook import WEBHOOK_FIELD_PLACEHOLDER
from apps.webhooks.presets.preset_options import WebhookPresetOptions
from apps.webhooks.utils import (
    InvalidWebhookData,
    InvalidWebhookHeaders,
    InvalidWebhookTrigger,
    InvalidWebhookUrl,
    serialize_event,
)
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from settings.base import WEBHOOK_RESPONSE_LIMIT

NOT_FROM_SELECTED_INTEGRATION = "Alert group was not from a selected integration"

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


EXECUTE_WEBHOOK_RETRIES = 3
# these exceptions are fully out of our control (e.g. customer's network issues)
# let's manually retry them without raising an exception
EXECUTE_WEBHOOK_EXCEPTIONS_TO_MANUALLY_RETRY = (requests.exceptions.Timeout,)
TRIGGER_TYPE_TO_LABEL = {
    Webhook.TRIGGER_ALERT_GROUP_CREATED: "alert group created",
    Webhook.TRIGGER_ACKNOWLEDGE: "acknowledge",
    Webhook.TRIGGER_RESOLVE: "resolve",
    Webhook.TRIGGER_SILENCE: "silence",
    Webhook.TRIGGER_UNSILENCE: "unsilence",
    Webhook.TRIGGER_UNRESOLVE: "unresolve",
    Webhook.TRIGGER_ESCALATION_STEP: "escalation",
    Webhook.TRIGGER_UNACKNOWLEDGE: "unacknowledge",
    Webhook.TRIGGER_STATUS_CHANGE: "status change",
}


class WebhookRequestStatus(typing.TypedDict):
    url: typing.Optional[str]
    request_trigger: typing.Optional[str]
    request_headers: typing.Optional[str]
    request_data: typing.Optional[str]
    status_code: typing.Optional[int]
    content: typing.Optional[str]
    webhook: Webhook
    event_data: str


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_webhook_event(trigger_type, alert_group_id, organization_id=None, user_id=None, is_backsync=False):
    from apps.webhooks.models import Webhook

    webhooks_qs = Webhook.objects.filter(
        trigger_type=trigger_type,
        organization_id=organization_id,
    ).exclude(is_webhook_enabled=False)
    # include status change triggered webhooks if needed
    if trigger_type in Webhook.STATUS_CHANGE_TRIGGERS:
        webhooks_qs |= Webhook.objects.filter(
            trigger_type=Webhook.TRIGGER_STATUS_CHANGE,
            organization_id=organization_id,
        ).exclude(is_webhook_enabled=False)

    if is_backsync:
        webhooks_qs = webhooks_qs.filter(is_from_connected_integration=False)

    for webhook in webhooks_qs:
        execute_webhook.apply_async((webhook.pk, alert_group_id, user_id, None), kwargs={"trigger_type": trigger_type})


def _isoformat_date(date_value: datetime) -> typing.Optional[str]:
    return date_value.isoformat() if date_value else None


def _build_payload(
    webhook: Webhook, alert_group: AlertGroup, user: User, trigger_type: int | None
) -> typing.Dict[str, typing.Any]:
    payload_trigger_type = webhook.trigger_type
    if payload_trigger_type == Webhook.TRIGGER_STATUS_CHANGE and trigger_type is not None:
        # use original trigger type when generating the payload if status change is set
        payload_trigger_type = trigger_type
    event = {
        "type": TRIGGER_TYPE_TO_LABEL[payload_trigger_type],
    }
    if payload_trigger_type == Webhook.TRIGGER_ALERT_GROUP_CREATED:
        event["time"] = _isoformat_date(alert_group.started_at)
    elif payload_trigger_type == Webhook.TRIGGER_ACKNOWLEDGE:
        event["time"] = _isoformat_date(alert_group.acknowledged_at)
    elif payload_trigger_type == Webhook.TRIGGER_RESOLVE:
        event["time"] = _isoformat_date(alert_group.resolved_at)
    elif payload_trigger_type == Webhook.TRIGGER_SILENCE:
        event["time"] = _isoformat_date(alert_group.silenced_at)
        event["until"] = _isoformat_date(alert_group.silenced_until)

    # include latest response data per webhook in the event input data
    # exclude past responses from webhook being executed
    responses_data = {}
    responses = (
        alert_group.webhook_responses.all()
        .exclude(webhook__public_primary_key=webhook.public_primary_key)
        .order_by("-timestamp")
    )
    for r in responses:
        if r.webhook.public_primary_key not in responses_data:
            try:
                response_data = r.json()
            except JSONDecodeError:
                response_data = r.content
            responses_data[r.webhook.public_primary_key] = response_data

    return serialize_event(event, alert_group, user, webhook, responses_data)


def mask_authorization_header(
    headers: typing.Dict[str, str], header_keys_to_mask: typing.List[str]
) -> typing.Dict[str, str]:
    masked_headers = headers.copy()
    lower_keys = set(k.lower() for k in header_keys_to_mask)
    for k in headers.keys():
        if k.lower() in lower_keys:
            masked_headers[k] = WEBHOOK_FIELD_PLACEHOLDER
    return masked_headers


def make_request(
    webhook: Webhook, alert_group: AlertGroup, data: typing.Dict[str, typing.Any]
) -> typing.Tuple[bool, WebhookRequestStatus, typing.Optional[str], typing.Optional[Exception]]:
    status: WebhookRequestStatus = {
        "url": None,
        "request_trigger": None,
        "request_headers": None,
        "request_data": None,
        "status_code": None,
        "content": None,
        "webhook": webhook,
        "event_data": json.dumps(data),
    }
    masked_header_keys = ["Authorization"]

    exception = error = None
    try:
        if webhook.preset:
            if webhook.preset not in WebhookPresetOptions.WEBHOOK_PRESETS:
                raise Exception(f"Invalid preset {webhook.preset}")
            else:
                preset = WebhookPresetOptions.WEBHOOK_PRESETS[webhook.preset]
                preset.override_parameters_at_runtime(webhook)
                masked_header_keys.extend(preset.get_masked_headers())

        if not webhook.check_integration_filter(alert_group):
            status["request_trigger"] = NOT_FROM_SELECTED_INTEGRATION
            return False, status, None, None

        triggered, status["request_trigger"] = webhook.check_trigger(data)
        if triggered:
            status["url"] = webhook.build_url(data)
            request_kwargs = webhook.build_request_kwargs(data, raise_data_errors=True)
            display_headers = mask_authorization_header(request_kwargs.get("headers", {}), masked_header_keys)
            status["request_headers"] = json.dumps(display_headers)
            if "json" in request_kwargs:
                status["request_data"] = json.dumps(request_kwargs["json"])
            else:
                status["request_data"] = request_kwargs.get("data")
            response = webhook.make_request(status["url"], request_kwargs)
            status["status_code"] = response.status_code
            content_length = len(response.content)
            if content_length <= WEBHOOK_RESPONSE_LIMIT:
                try:
                    status["content"] = json.dumps(response.json())
                except JSONDecodeError:
                    status["content"] = response.content.decode("utf-8")
            else:
                status[
                    "content"
                ] = f"Response content {content_length} exceeds {WEBHOOK_RESPONSE_LIMIT} character limit"

        return triggered, status, None, None
    except InvalidWebhookUrl as e:
        status["url"] = error = e.message
    except InvalidWebhookTrigger as e:
        status["request_trigger"] = error = e.message
    except InvalidWebhookHeaders as e:
        status["request_headers"] = error = e.message
    except InvalidWebhookData as e:
        status["request_data"] = error = e.message
    except Exception as e:
        status["content"] = error = str(e)
        exception = e

    return True, status, error, exception


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else EXECUTE_WEBHOOK_RETRIES
)
def execute_webhook(webhook_pk, alert_group_id, user_id, escalation_policy_id, trigger_type=None, manual_retry_num=0):
    from apps.webhooks.models import Webhook

    try:
        webhook = Webhook.objects.get(pk=webhook_pk)
    except Webhook.DoesNotExist:
        logger.warning(f"Webhook {webhook_pk} does not exist")
        return

    try:
        personal_log_records = UserNotificationPolicyLogRecord.objects.filter(
            alert_group_id=alert_group_id,
            author__isnull=False,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
        ).select_related("author")
        alert_group = (
            AlertGroup.objects.prefetch_related(
                Prefetch("personal_log_records", queryset=personal_log_records, to_attr="sent_notifications")
            )
            .select_related("channel")
            .get(pk=alert_group_id)
        )
    except AlertGroup.DoesNotExist:
        return

    user = None
    if user_id is not None:
        user = User.objects.filter(pk=user_id).first()

    data = _build_payload(webhook, alert_group, user, trigger_type)
    triggered, status, error, exception = make_request(webhook, alert_group, data)

    # create response entry only if webhook was triggered
    if triggered:
        WebhookResponse.objects.create(
            alert_group=alert_group,
            trigger_type=trigger_type or webhook.trigger_type,
            **status,
        )
    else:
        reason = status.get("request_trigger", "Unknown")
        logger.info(f"Webhook {webhook_pk} was not triggered: {reason}")

    escalation_policy = step = None
    if escalation_policy_id:
        escalation_policy = EscalationPolicy.objects.filter(pk=escalation_policy_id).first()
        step = EscalationPolicy.STEP_TRIGGER_CUSTOM_WEBHOOK

    # create log record
    error_code = None
    log_type = AlertGroupLogRecord.TYPE_CUSTOM_WEBHOOK_TRIGGERED
    reason = str(status["status_code"])
    if error is not None:
        log_type = AlertGroupLogRecord.TYPE_ESCALATION_FAILED
        error_code = AlertGroupLogRecord.ERROR_ESCALATION_TRIGGER_CUSTOM_WEBHOOK_ERROR
        reason = error

    if triggered:
        AlertGroupLogRecord.objects.create(
            type=log_type,
            alert_group=alert_group,
            author=user,
            reason=reason,
            step_specific_info={
                "webhook_name": webhook.name,
                "webhook_id": webhook.public_primary_key,
                "trigger": TRIGGER_TYPE_TO_LABEL[webhook.trigger_type],
            },
            escalation_policy=escalation_policy,
            escalation_policy_step=step,
            escalation_error_code=error_code,
        )

    if isinstance(exception, EXECUTE_WEBHOOK_EXCEPTIONS_TO_MANUALLY_RETRY):
        msg_details = (
            f"webhook={webhook_pk} alert_group={alert_group_id} user={user_id} escalation_policy={escalation_policy_id}"
        )

        if manual_retry_num < EXECUTE_WEBHOOK_RETRIES:
            retry_num = manual_retry_num + 1
            logger.warning(f"Manually retrying execute_webhook for {msg_details} manual_retry_num={retry_num}")
            execute_webhook.apply_async(
                (webhook_pk, alert_group_id, user_id, escalation_policy_id),
                kwargs={"trigger_type": trigger_type, "manual_retry_num": retry_num},
                countdown=10,
            )
        else:
            # don't raise an exception if we've exhausted retries for
            # exceptions within EXECUTE_WEBHOOK_EXCEPTIONS_TO_MANUALLY_RETRY, simply give up trying
            logger.warning(f"Exhausted execute_webhook retries for {msg_details}")
    elif exception:
        raise exception
