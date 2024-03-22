import datetime
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.schedules.models import CustomOnCallShift, OnCallScheduleICal, OnCallScheduleWeb
from apps.schedules.tasks.refresh_ical_files import refresh_ical_file, start_refresh_ical_files


@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_no_out_of_office_events():
    pass


@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_full_day_out_of_office_event():
    pass


@pytest.mark.django_db
def test_sync_out_of_office_calendar_events_for_user_partial_day_out_of_office_event():
    pass
