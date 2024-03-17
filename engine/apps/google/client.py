import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleCalendarAPIClient:
    def __init__(self, refresh_token: str):
        """
        https://developers.google.com/calendar/api/quickstart/python
        https://google-auth.readthedocs.io/en/stable/reference/google.oauth2.credentials.html
        """

        # token (Optional(str)) – The OAuth 2.0 access token. Can be None if refresh information is provided.
        credentials = Credentials(token=None, refresh_token=refresh_token)

        if not credentials or not credentials.valid:
            print("credentials not valid", credentials, credentials.valid)
            credentials.refresh(Request())

        self.service = build("calendar", "v3", credentials=credentials)

    def fetch_out_of_office_events(self) -> None:
        """
        https://developers.google.com/calendar/api/v3/reference/events/list
        """
        print("Getting the upcoming 10 events")

        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=datetime.datetime.now(datetime.UTC).isoformat() + "Z",  # 'Z' indicates UTC time,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
                eventTypes="outOfOffice",
            )
            .execute()
        )
        events = events_result.get("items", [])

        print("events are", events)
