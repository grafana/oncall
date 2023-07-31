from celery.utils.log import get_task_logger

from common.custom_celery_tasks import shared_dedicated_queue_retry_task

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task()
def create_shift_swap_request_message(shift_swap_request_pk: str) -> None:
    from apps.schedules.models import ShiftSwapRequest
    from apps.slack.scenarios.shift_swap_requests import BaseShiftSwapRequestStep

    task_logger.info(f"Start create_shift_swap_request_message: pk = {shift_swap_request_pk}")

    try:
        shift_swap_request = ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        task_logger.info(
            f"Tried to create_shift_swap_request_message for non-existing shift swap request {shift_swap_request_pk}"
        )
        return

    if shift_swap_request.slack_channel_id is None:
        task_logger.info(
            f"Skipping create_shift_swap_request_message for shift_swap_request {shift_swap_request_pk} because channel_id is None"
        )
        return

    organization = shift_swap_request.organization

    step = BaseShiftSwapRequestStep(organization.slack_team_identity, organization)
    slack_message = step.create_message(shift_swap_request)

    shift_swap_request.slack_message = slack_message
    shift_swap_request.save(update_fields=["slack_message"])


@shared_dedicated_queue_retry_task()
def update_shift_swap_request_message(shift_swap_request_pk: str) -> None:
    from apps.schedules.models import ShiftSwapRequest
    from apps.slack.scenarios.shift_swap_requests import BaseShiftSwapRequestStep

    task_logger.info(f"Start update_shift_swap_request_message: pk = {shift_swap_request_pk}")

    try:
        # NOTE: need to use objects_with_deleted here because we may be updating the slack message
        # for a swap request that was deleted
        shift_swap_request = ShiftSwapRequest.objects_with_deleted.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        task_logger.info(
            f"Tried to update_shift_swap_request_message for non-existing shift swap request {shift_swap_request_pk}"
        )
        return

    if shift_swap_request.slack_channel_id is None:
        task_logger.info(
            f"Skipping update_shift_swap_request_message for shift_swap_request {shift_swap_request_pk} because channel_id is None"
        )
        return

    organization = shift_swap_request.organization

    step = BaseShiftSwapRequestStep(organization.slack_team_identity, organization)
    step.update_message(shift_swap_request)
