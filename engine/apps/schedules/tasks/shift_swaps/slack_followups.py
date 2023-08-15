import datetime

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.schedules.models import ShiftSwapRequest
from apps.slack.scenarios.shift_swap_requests import ShiftSwapRequestFollowUp
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

task_logger = get_task_logger(__name__)

FOLLOWUP_OFFSETS = [
    datetime.timedelta(weeks=4),
    datetime.timedelta(weeks=3),
    datetime.timedelta(weeks=2),
    datetime.timedelta(weeks=1),
    datetime.timedelta(days=3),
    datetime.timedelta(days=2),
    datetime.timedelta(days=1),
    datetime.timedelta(hours=12),
]
FOLLOWUP_WINDOW = datetime.timedelta(hours=1)


@shared_dedicated_queue_retry_task()
def send_shift_swap_request_slack_followups() -> None:
    for shift_swap_request_pk in _get_shift_swap_request_pks_in_followup_window(timezone.now()):
        send_shift_swap_request_slack_followup.delay(shift_swap_request_pk)


def _get_shift_swap_request_pks_in_followup_window(now: datetime.datetime) -> list[int]:
    shift_swap_requests_in_notification_window = []
    for shift_swap_request in ShiftSwapRequest.objects.filter(benefactor__isnull=True, swap_start__gt=now).only(
        "pk", "swap_start"
    ):
        for offset in FOLLOWUP_OFFSETS:
            notification_window_start = shift_swap_request.swap_start - offset
            notification_window_end = notification_window_start + FOLLOWUP_WINDOW

            if notification_window_start <= now <= notification_window_end:
                shift_swap_requests_in_notification_window.append(shift_swap_request.pk)
                break

    return shift_swap_requests_in_notification_window


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def send_shift_swap_request_slack_followup(shift_swap_request_pk: int) -> None:
    try:
        shift_swap_request = ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        task_logger.warning(f"ShiftSwapRequest {shift_swap_request_pk} does not exist")
        return

    if shift_swap_request.slack_channel_id is None:
        task_logger.warning(f"ShiftSwapRequest {shift_swap_request_pk} does not have an associated Slack channel")
        return

    if _has_followup_been_sent(shift_swap_request):
        task_logger.info(f"ShiftSwapRequest {shift_swap_request_pk} followup has already been sent")
        return
    _mark_followup_sent(shift_swap_request)

    task_logger.info(f"Sending Slack followup for ShiftSwapRequest {shift_swap_request_pk}")
    step = ShiftSwapRequestFollowUp(
        shift_swap_request.organization.slack_team_identity, shift_swap_request.organization
    )
    step.post_message(shift_swap_request)


def _has_followup_been_sent(shift_swap_request: ShiftSwapRequest) -> bool:
    key = _followup_cache_key(shift_swap_request)
    return cache.get(key) is True


def _mark_followup_sent(shift_swap_request: ShiftSwapRequest) -> None:
    key = _followup_cache_key(shift_swap_request)
    cache.set(key, True, timeout=FOLLOWUP_WINDOW.total_seconds())


def _followup_cache_key(shift_swap_request: ShiftSwapRequest) -> str:
    return f"ssr_slack_followup:{shift_swap_request.pk}"
