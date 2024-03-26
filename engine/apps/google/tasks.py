import logging

from celery.utils.log import get_task_logger

from apps.google.client import GoogleCalendarAPIClient
from apps.google.models import GoogleOAuth2User
from apps.schedules.models import OnCallSchedule, ShiftSwapRequest
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_user(google_oauth2_user_pk: int) -> None:
    """
    TODO: this is suppeerrr inefficient, having these nested for loops run, for each user, every 30 mins.. optimize this

    QUESTION: will we need to persist any information about these calendar events in our database?
    """
    google_oauth2_user = GoogleOAuth2User.objects.get(pk=google_oauth2_user_pk)
    google_api_client = GoogleCalendarAPIClient(google_oauth2_user.access_token, google_oauth2_user.refresh_token)

    user = google_oauth2_user.user
    user_id = user.pk

    logger.info(f"Syncing out of office Google Calendar events for user {user_id}")

    user_google_calendar_settings = user.google_calendar_settings
    specific_oncall_schedules_to_sync = user_google_calendar_settings["specific_oncall_schedules_to_sync"]

    users_schedules = OnCallSchedule.objects.related_to_user(user)
    if specific_oncall_schedules_to_sync:
        users_schedules = users_schedules.filter(public_primary_key__in=specific_oncall_schedules_to_sync)

    for out_of_office_event in google_api_client.fetch_out_of_office_events():
        event_id = out_of_office_event.raw_event["id"]
        start_time_utc = out_of_office_event.start_time_utc
        end_time_utc = out_of_office_event.end_time_utc

        logger.info(
            f"Processing out of office event {event_id} starting at {start_time_utc} and ending at "
            f"{end_time_utc} for user {user_id}"
        )

        for schedule in users_schedules:
            # print("Yooooo", start_time_utc, end_time_utc)

            _, _, upcoming_shifts = schedule.shifts_for_user(
                user,
                start_time_utc,
                datetime_end=end_time_utc,
            )

            if upcoming_shifts:
                logger.info(
                    f"Found {len(upcoming_shifts)} upcoming shift(s) for user {user_id} "
                    f"during the out of office event {event_id}"
                )

                # print(upcoming_shifts)

                # TODO: check if a shift swap request already exists for this user, schedule, and time range
                ShiftSwapRequest.objects.create(
                    beneficiary=user,
                    schedule=schedule,
                    swap_start=start_time_utc,
                    swap_end=end_time_utc,
                    description=f"{user.name or user.email} will be out of office during this time according to Google Calendar",
                )
            else:
                logger.info(
                    f"No upcoming shifts found for user {user_id} during the out of office event {event_id}"
                )


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True)
def sync_out_of_office_calendar_events_for_all_users() -> None:
    for google_oauth2_user in GoogleOAuth2User.objects.all():
        sync_out_of_office_calendar_events_for_user.apply_async(args=(google_oauth2_user.pk,))
