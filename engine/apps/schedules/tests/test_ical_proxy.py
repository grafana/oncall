from datetime import datetime

import pytz
from django.utils import timezone

from apps.schedules.ical_events import ical_events


def test_recurring_ical_events(get_ical):
    calendar = get_ical("calendar_with_recurring_event.ics")
    day_to_check_iso = "2021-01-27T15:27:14.448059+00:00"
    day_to_check = timezone.datetime.fromisoformat(day_to_check_iso)
    events = ical_events.get_events_from_ical_between(
        calendar,
        day_to_check - timezone.timedelta(days=1),
        day_to_check + timezone.timedelta(days=1),
    )
    assert len(events) == 3
    assert events[0]["SUMMARY"] == "@Bernard Desruisseaux"
    assert events[1]["SUMMARY"] == "@Bernard Desruisseaux"
    assert events[2]["SUMMARY"] == "@Bernard Desruisseaux"


def test_recurring_ical_events_with_edited_event(get_ical):
    calendar = get_ical("calendar_with_edited_recurring_events.ics")
    day_to_check_iso = "2021-01-27T15:27:14.448059+00:00"
    day_to_check = timezone.datetime.fromisoformat(day_to_check_iso)
    events = ical_events.get_events_from_ical_between(
        calendar,
        day_to_check - timezone.timedelta(days=1),
        day_to_check + timezone.timedelta(days=1),
    )
    assert len(events) == 3
    assert events[0]["SUMMARY"] == "@Bob"
    assert events[1]["SUMMARY"] == "@Bernard Desruisseaux"
    assert events[2]["SUMMARY"] == "@Bernard Desruisseaux"


def test_recurring_ical_events_with_all_day_event(get_ical):
    calendar = get_ical("calendar_with_all_day_event.ics")
    day_to_check_iso = "2021-01-27T15:27:14.448059+00:00"
    parsed_iso_day_to_check = datetime.fromisoformat(day_to_check_iso).replace(tzinfo=pytz.UTC)
    events = ical_events.get_events_from_ical_between(
        calendar,
        parsed_iso_day_to_check - timezone.timedelta(days=1),
        parsed_iso_day_to_check + timezone.timedelta(days=1),
    )
    assert len(events) == 5
    assert events[0]["SUMMARY"] == "@Alex"
    assert events[1]["SUMMARY"] == "@Alice"
    assert events[2]["SUMMARY"] == "@Bob"
    assert events[3]["SUMMARY"] == "@Bernard Desruisseaux"
    assert events[4]["SUMMARY"] == "@Bernard Desruisseaux"
