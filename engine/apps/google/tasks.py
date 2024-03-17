import logging
import typing

from celery.utils.log import get_task_logger

from apps.google.client import GoogleCalendarAPIClient
from apps.user_management.models import User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_user(user_pk: int) -> None:
    user = User.objects.get(pk=user_pk)
    google_api_client = GoogleCalendarAPIClient(user.google_oauth2_user.refresh_token)
    google_api_client.fetch_out_of_office_events()

    # TODO: persist the out of office events in our database + generate shift swap requests from these events


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_all_users() -> None:
    for user in User.objects.filter(google_oauth2_user__isnull=False):
        sync_out_of_office_calendar_events_for_user.apply_async(args=(user.pk,))
