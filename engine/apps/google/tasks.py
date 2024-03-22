import logging
import pprint

from celery.utils.log import get_task_logger

from apps.google.client import GoogleCalendarAPIClient
from apps.google.models import GoogleOAuth2User
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_user(google_oauth2_user_pk: int) -> None:
    google_oauth2_user = GoogleOAuth2User.objects.get(pk=google_oauth2_user_pk)
    google_api_client = GoogleCalendarAPIClient(google_oauth2_user.access_token, google_oauth2_user.refresh_token)

    # NOTE: shift swap request generation will be done in https://github.com/grafana/oncall-private/issues/2590
    # QUESTION: will we need to persist any information about these calendar events in our database?
    _out_of_office_events = google_api_client.fetch_out_of_office_events()



@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_all_users() -> None:
    for google_oauth2_user in GoogleOAuth2User.objects.all():
        sync_out_of_office_calendar_events_for_user.apply_async(args=(google_oauth2_user.pk,))
