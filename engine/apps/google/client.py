import datetime
import logging
import typing

from django.conf import settings
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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


class _GoogleCalendarHTTPError(Exception):
    def __init__(self, http_error) -> None:
        self.error = http_error


class GoogleCalendarGenericHTTPError(_GoogleCalendarHTTPError):
    """Raised when a generic HTTP error occurs when communicating with the Google Calendar API"""


class GoogleCalendarUnauthorizedHTTPError(_GoogleCalendarHTTPError):
    """Raised when an HTTP 403 error occurs when communicating with the Google Calendar API"""


class GoogleCalendarRefreshError(Exception):
    def __init__(self, refresh_error) -> None:
        self.error = refresh_error


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

        try:
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
        except HttpError as e:
            if e.status_code == 403:
                # this scenario can be encountered when, the OAuth2 token that we have
                # does not contain the https://www.googleapis.com/auth/calendar.events.readonly scope
                # example error:
                # <HttpError 403 when requesting https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin=2024-08-08T14%3A00%3A00%2B0000&timeMax=2024-09-07T14%3A00%3A00%2B0000&maxResults=250&singleEvents=true&orderBy=startTime&eventTypes=outOfOffice&alt=json returned "Request had insufficient authentication scopes.". Details: "[{'message': 'Insufficient Permission', 'domain': 'global', 'reason': 'insufficientPermissions'}]"> # noqa: E501
                #
                # this should really only occur for tokens granted prior to this commit (which wrote this comment).
                # Before then we didn't handle the scenario where the Google oauth consent screen could potentially
                # have checkboxes and users would have to actively check the checkbox to grant this scope. We now
                # handle this scenario.
                #
                # References
                # https://jpassing.com/2022/08/01/dealing-with-partial-consent-in-google-oauth-clients/
                # https://raintank-corp.slack.com/archives/C05AMEGMLCT/p1723556508149689
                # https://raintank-corp.slack.com/archives/C04JCU51NF8/p1723493330369349
                logger.error(f"GoogleCalendarAPIClient - HttpError 403 when fetching out of office events: {e}")
                raise GoogleCalendarUnauthorizedHTTPError(e)

            logger.error(f"GoogleCalendarAPIClient - HttpError when fetching out of office events: {e}")
            raise GoogleCalendarGenericHTTPError(e)
        except RefreshError as e:
            # we see RefreshError in two different scenarios:
            # 1. RefreshError('invalid_grant: Account has been deleted', {'error': 'invalid_grant', 'error_description': 'Account has been deleted'})
            # 2. RefreshError('invalid_grant: Token has been expired or revoked.', {'error': 'invalid_grant', 'error_description': 'Token has been expired or revoked.'})
            #
            # https://stackoverflow.com/a/49024030/3902555
            #
            # in both of these cases the granted token is no longer good and we should delete it

            try:
                error_details = e.args[1]  # should be a dict like in the comment above
            except IndexError:
                error_details = None  # catch this just in case

            error_description = error_details.get("error_description") if error_details else None

            logger.error(
                f"GoogleCalendarAPIClient - RefreshError when fetching out of office events: {e} "
                f"error_description={error_description}"
            )
            raise GoogleCalendarRefreshError(e)

        return [GoogleCalendarEvent(event) for event in events_result.get("items", [])]
