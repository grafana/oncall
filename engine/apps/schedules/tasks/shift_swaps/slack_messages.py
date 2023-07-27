from celery.utils.log import get_task_logger

from apps.slack.scenarios.scenario_step import ScenarioStep
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

task_logger = get_task_logger(__name__)


@shared_dedicated_queue_retry_task()
def post_shift_swap_request_creation_message(shift_swap_request_pk):
    from apps.schedules.models import ShiftSwapRequest

    task_logger.info(f"Start post_shift_swap_creation_message: pk = {shift_swap_request_pk}")

    try:
        shift_swap_request = ShiftSwapRequest.objects.get(pk=shift_swap_request_pk)
    except ShiftSwapRequest.DoesNotExist:
        task_logger.info(
            f"Tried to post_shift_swap_request_creation_message for non-existing shift swap request {shift_swap_request_pk}"
        )
        return

    schedule = shift_swap_request.schedule
    organization = schedule.organization

    ShiftSwapRequestCreationStep = ScenarioStep.get_step("shift_swap_requests", "ShiftSwapRequestCreationStep")
    step = ShiftSwapRequestCreationStep(organization.slack_team_identity, organization)
    step.send_creation_message(shift_swap_request)
