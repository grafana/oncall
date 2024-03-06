import datetime

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.schedules.models import ShiftSwapRequest
from apps.slack.scenarios.shift_swap_requests import ShiftSwapRequestFollowUp
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

task_logger = get_task_logger(__name__)

# FOLLOWUP_WINDOW is used by _get_shift_swap_requests_in_followup_window and _mark_followup_sent to:
# 1. Determine which SSRs to send followups for when the periodic task is run
# 2. Prevent sending multiple followups for a single SSRS in a short period
FOLLOWUP_WINDOW = datetime.timedelta(hours=1)


@shared_dedicated_queue_retry_task()
def send_shift_swap_request_slack_followups() -> None:
    """A periodic task to send Slack followups for shift swap requests."""

    for shift_swap_request in _get_shift_swap_requests_in_followup_window(timezone.now()):
        if not _has_followup_been_sent(shift_swap_request):
            send_shift_swap_request_slack_followup.delay(shift_swap_request.pk)
            _mark_followup_sent(shift_swap_request)


def _get_shift_swap_requests_in_followup_window(now: datetime.datetime) -> list[ShiftSwapRequest]:
    """Get all SSRs that are in the followup window."""

    shift_swap_requests_in_notification_window = []
    for shift_swap_request in ShiftSwapRequest.objects.get_open_requests(now):
        for offset in ShiftSwapRequest.FOLLOWUP_OFFSETS:
            notification_window_start = shift_swap_request.swap_start - offset
            notification_window_end = notification_window_start + FOLLOWUP_WINDOW

            if notification_window_start <= now <= notification_window_end:
                shift_swap_requests_in_notification_window.append(shift_swap_request)
                break

    return shift_swap_requests_in_notification_window


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else 10
)
def send_shift_swap_request_slack_followup(shift_swap_request_pk: int) -> None:
    """Send a Slack followup message for a particular SSR."""

    try:
        shift_swap_request = ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        task_logger.warning(f"ShiftSwapRequest {shift_swap_request_pk} does not exist")
        return

    if shift_swap_request.slack_channel_id is None:
        task_logger.warning(f"ShiftSwapRequest {shift_swap_request_pk} does not have an associated Slack channel")
        return

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
