import os

import pytest
from icalendar import Calendar

CALENDARS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendars")


@pytest.fixture()
def get_ical():
    def _get_ical(calendar_name):
        path_to_calendar = os.path.join(CALENDARS_FOLDER, calendar_name)
        with open(path_to_calendar, "rb") as file:
            content = file.read()
            return Calendar.from_ical(content)

    return _get_ical
