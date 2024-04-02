import datetime
import logging
import typing

from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from apps.google import constants, utils
from apps.google.types import GoogleCalendarEvent as GoogleCalendarEventType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GoogleCalendarEvent:
    def __init__(self, event: GoogleCalendarEventType):
        self.raw_event = event
        self._start_time = utils.datetime_strptime(event["start"]["dateTime"])
        self._end_time = utils.datetime_strptime(event["end"]["dateTime"])

        self.start_time_utc = self._start_time.astimezone(datetime.timezone.utc)
        self.end_time_utc = self._end_time.astimezone(datetime.timezone.utc)


class GoogleCalendarAPIClient:
    MAX_NUMBER_OF_CALENDAR_EVENTS_TO_FETCH = 250
    """
    By default the value is 250 events. The page size can never be larger than 2500 events
    """

    CALENDAR_ID = "primary"
    """
    for right now we only consider the user's primary calendar. If in the future we
    want to allow the user to specify a different calendar, we'd need to [retrieve all their calendars](https://developers.google.com/calendar/v3/reference/calendarList/list)
    , display this list to them + perist their choice

    See `calendarId` under the "Parameters" section [here](https://developers.google.com/calendar/api/v3/reference/events/list)
    """

    def __init__(self, access_token: str, refresh_token: str):
        """
        https://developers.google.com/calendar/api/quickstart/python
        https://google-auth.readthedocs.io/en/stable/reference/google.oauth2.credentials.html
        """
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://www.googleapis.com/oauth2/v3/token",
            client_id=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
            client_secret=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
        )

        self.service = build("calendar", "v3", credentials=credentials)

    def fetch_out_of_office_events(self) -> typing.List[GoogleCalendarEvent]:
        """
        https://developers.google.com/calendar/api/v3/reference/events/list
        """
        logger.info(
            f"GoogleCalendarAPIClient - Getting the upcoming {self.MAX_NUMBER_OF_CALENDAR_EVENTS_TO_FETCH} "
            "out of office events"
        )

        now = datetime.datetime.now(datetime.UTC)
        time_min = utils.datetime_strftime(now)
        time_max = utils.datetime_strftime(
            now + datetime.timedelta(days=constants.DAYS_IN_FUTURE_TO_CONSIDER_OUT_OF_OFFICE_EVENTS)
        )

        events_result = (
            self.service.events()
            .list(
                calendarId=self.CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=self.MAX_NUMBER_OF_CALENDAR_EVENTS_TO_FETCH,
                singleEvents=True,
                orderBy="startTime",
                eventTypes="outOfOffice",
            )
            .execute()
        )
        return [GoogleCalendarEvent(event) for event in events_result.get("items", [])]
