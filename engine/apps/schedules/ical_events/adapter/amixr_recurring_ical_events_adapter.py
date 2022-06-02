from collections import defaultdict
from datetime import datetime
from typing import List

from django.utils import timezone
from icalendar import Calendar, Event
from recurring_ical_events import UnfoldableCalendar, compare_greater, is_event, time_span_contains_event

from apps.schedules.ical_events.proxy.ical_proxy import IcalService

EXTRA_LOOKUP_DAYS = 16


class AmixrUnfoldableCalendar(UnfoldableCalendar):
    """
    This is overridden recurring_ical_events.UnfoldableCalendar.
    It is overridden because of bug when summary of recurring event stay the same after editing.
    In recurring-ical-events==0.1.20b0 this problem is fixed, but all-day events without timezone lead to exception.
    So i took part of code from 0.1.20b0 but leave 0.1.16b in requirements.
    """

    def between(self, start, stop):
        """Return events at a time between start (inclusive) and end (inclusive)"""
        span_start = self.to_datetime(start)
        span_stop = self.to_datetime(stop)
        events = []
        events_by_id = defaultdict(dict)  # UID (str) : RECURRENCE-ID(datetime) : event (Event)
        default_uid = object()

        def add_event(event):
            """Add an event and check if it was edited."""
            same_events = events_by_id[event.get("UID", default_uid)]
            recurrence_id = event.get("RECURRENCE-ID", event["DTSTART"]).dt
            # Start of code from 0.1.20b0
            if isinstance(recurrence_id, datetime):
                recurrence_id = recurrence_id.date()
            other = same_events.get(recurrence_id, None)
            if other:
                event_recurrence_id = event.get("RECURRENCE-ID", None)
                other_recurrence_id = other.get("RECURRENCE-ID", None)
                if event_recurrence_id is not None and other_recurrence_id is None:
                    events.remove(other)
                elif event_recurrence_id is None and other_recurrence_id is not None:
                    return
                else:
                    event_sequence = event.get("SEQUENCE", None)
                    other_sequence = other.get("SEQUENCE", None)
                    if event_sequence is not None and other_sequence is not None:
                        if event["SEQUENCE"] < other["SEQUENCE"]:
                            return
                        events.remove(other)
            # End of code from 0.1.20b0
            same_events[recurrence_id] = event
            events.append(event)

        for event in self.calendar.walk():
            if not is_event(event):
                continue
            repetitions = self.RepeatedEvent(event, span_start)
            for repetition in repetitions:
                if compare_greater(repetition.start, span_stop):
                    break
                if repetition.is_in_span(span_start, span_stop):
                    add_event(repetition.as_vevent())
        return events


class AmixrRecurringIcalEventsAdapter(IcalService):
    def get_events_from_ical_between(self, calendar: Calendar, start_date: datetime, end_date: datetime) -> List[Event]:
        """
        EXTRA_LOOKUP_DAYS introduced to solve bug when swapping two recurrent events with each other lead
        to their duplicates in case end_date - start_date < recurrent_event duration.
        It is happening because for such swap new event is created in ical with same RECURRENCE_ID as original and greater SEQUENCE param.
        If one of these events misses lookup window we can't to take into account SEQUENCE value
        and use only event with higher SEQUENCE value.
        Solution is to lookup for EXTRA_LOOKUP_DAYS forward and back and then
        make one more pass for events array to filter out events which are between start_date and end_date.
        EXTRA_LOOKUP_DAYS is empirical.
        """
        events = AmixrUnfoldableCalendar(calendar).between(
            start_date - timezone.timedelta(days=EXTRA_LOOKUP_DAYS),
            end_date + timezone.timedelta(days=EXTRA_LOOKUP_DAYS),
        )

        def filter_extra_days(event):
            return time_span_contains_event(start_date, end_date, event["DTSTART"].dt, event["DTEND"].dt)

        return list(filter(filter_extra_days, events))
