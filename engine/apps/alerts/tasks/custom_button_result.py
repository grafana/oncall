import json
import logging

from django.conf import settings
from django.db import transaction
from jinja2 import TemplateError

from apps.alerts.utils import request_outgoing_webhook
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

from .send_alert_group_signal import send_alert_group_signal
from .task_logger import task_logger

logger = logging.getLogger(__name__)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def custom_button_result(custom_button_pk, alert_group_pk, user_pk=None, escalation_policy_pk=None):
    from apps.alerts.models import AlertGroup, AlertGroupLogRecord, CustomButton, EscalationPolicy
    from apps.user_management.models import User

    task_logger.debug(
        f"Start custom_button_result for alert_group {alert_group_pk}, " f"custom_button {custom_button_pk}"
    )
    try:
        custom_button = CustomButton.objects.get(pk=custom_button_pk)
    except CustomButton.DoesNotExist:
        task_logger.info(f"Custom_button {custom_button_pk} for alert_group {alert_group_pk} does not exist")
        return

    alert_group = AlertGroup.objects.filter(pk=alert_group_pk)[0]
    escalation_policy = EscalationPolicy.objects.filter(pk=escalation_policy_pk).first()
    task_logger.debug(
        f"Start getting data for request in custom_button_result task for alert_group {alert_group_pk}, "
        f"custom_button {custom_button_pk}"
    )

    first_alert = alert_group.alerts.first()

    try:
        post_kwargs = custom_button.build_post_kwargs(first_alert)
    except TemplateError:
        is_request_successful = False
        result_message = "Template error"
    except json.JSONDecodeError:
        is_request_successful = False
        result_message = "JSON decoding error"
    else:
        is_request_successful, result_message = request_outgoing_webhook(
            custom_button.webhook, "POST", post_kwargs=post_kwargs
        )

    task_logger.debug(
        f"Send post request in custom_button_result task for alert_group {alert_group_pk}, "
        f"custom_button {custom_button_pk}"
    )
    with transaction.atomic():
        user = None
        if user_pk:
            user = User.objects.get(pk=user_pk)

        log_record = AlertGroupLogRecord(
            type=AlertGroupLogRecord.TYPE_CUSTOM_BUTTON_TRIGGERED,
            alert_group=alert_group,
            custom_button=custom_button,
            author=user,
            reason=result_message,
            step_specific_info={
                "custom_button_name": custom_button.name,
                "is_request_successful": is_request_successful,
            },
            escalation_policy=escalation_policy,
            escalation_policy_step=EscalationPolicy.STEP_TRIGGER_CUSTOM_BUTTON,
        )
        log_record.save()
        task_logger.debug(
            f"call send_alert_group_signal for alert_group {alert_group_pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}'"
        )
        transaction.on_commit(lambda: send_alert_group_signal.apply_async((log_record.pk,)))
    task_logger.debug(f"Finish custom_button_result for alert_group {alert_group_pk}, custom_button {custom_button_pk}")
