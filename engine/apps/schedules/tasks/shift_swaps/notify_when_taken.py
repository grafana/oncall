from celery.utils.log import get_task_logger

from apps.mobile_app.tasks import (
    notify_beneficiary_about_taken_shift_swap_request as notify_beneficiary_about_taken_shift_swap_request_via_push_notification,
)
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task()
def notify_beneficiary_about_taken_shift_swap_request(shift_swap_request_pk: str) -> None:
    from apps.schedules.models import ShiftSwapRequest
    from apps.slack.scenarios.shift_swap_requests import AcceptShiftSwapRequestStep

    task_logger.info(f"Start notify_beneficiary_about_taken_shift_swap_request: pk = {shift_swap_request_pk}")

    try:
        shift_swap_request = ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        task_logger.info(
            f"Tried to notify_beneficiary_about_taken_shift_swap_request for non-existing shift swap request {shift_swap_request_pk}"
        )
        return

    if shift_swap_request.slack_channel_id is None:
        task_logger.info(
            f"Skipping notify_beneficiary_about_taken_shift_swap_request for shift_swap_request {shift_swap_request_pk} because channel_id is None"
        )
        return

    organization = shift_swap_request.organization
    step = AcceptShiftSwapRequestStep(organization.slack_team_identity, organization)
    step.post_request_taken_message_to_thread(shift_swap_request)

    notify_beneficiary_about_taken_shift_swap_request_via_push_notification.apply_async((shift_swap_request_pk,))
