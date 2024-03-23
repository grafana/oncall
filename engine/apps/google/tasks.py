import logging

from celery.utils.log import get_task_logger

from apps.google import constants
from apps.google.client import GoogleCalendarAPIClient
from apps.google.models import GoogleOAuth2User
from apps.schedules.models import OnCallSchedule
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_user(google_oauth2_user_pk: int) -> None:
    google_oauth2_user = GoogleOAuth2User.objects.get(pk=google_oauth2_user_pk)
    user = google_oauth2_user.user
    user_id = user.pk
    users_schedules = OnCallSchedule.objects.related_to_user(user)

    google_api_client = GoogleCalendarAPIClient(google_oauth2_user.access_token, google_oauth2_user.refresh_token)

    logger.info(f"Syncing out of office Google Calendar events for user {user_id}")

    # TODO: this is suppeerrr inefficient, having these nested for loops run, for each user, every 30 mins
    # optimize this
    #
    # QUESTION: will we need to persist any information about these calendar events in our database?
    for out_of_office_event in google_api_client.fetch_out_of_office_events():
        event_id = out_of_office_event.raw_event["id"]
        start_time = out_of_office_event.start_time
        end_time = out_of_office_event.end_time

        logger.info(
            f"Processing out of office event {event_id} starting at {start_time} and ending at "
            f"{end_time} for user {user_id}"
        )

        for schedule in users_schedules:
            oncall_shifts = schedule.shifts_for_user(user, start_time, constants.DAYS_IN_FUTURE_TO_CONSIDER_OUT_OF_OFFICE_EVENTS)

            print("oncall_shifts", oncall_shifts)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_all_users() -> None:
    for google_oauth2_user in GoogleOAuth2User.objects.all():
        sync_out_of_office_calendar_events_for_user.apply_async(args=(google_oauth2_user.pk,))
