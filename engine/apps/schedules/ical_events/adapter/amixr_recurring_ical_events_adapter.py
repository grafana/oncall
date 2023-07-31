import datetime
import re
import typing
from collections import defaultdict

from icalendar import Calendar, Event
from recurring_ical_events import UnfoldableCalendar, compare_greater, is_event, time_span_contains_event

from apps.schedules.constants import (
    ICAL_DATETIME_END,
    ICAL_DATETIME_STAMP,
    ICAL_DATETIME_START,
    ICAL_RRULE,
    ICAL_UID,
    ICAL_UNTIL,
    RE_EVENT_UID_V1,
    RE_EVENT_UID_V2,
)
from apps.schedules.ical_events.proxy.ical_proxy import IcalService

EXTRA_LOOKUP_DAYS = 16


class AmixrUnfoldableCalendar(UnfoldableCalendar):
    """
    This is overridden recurring_ical_events.UnfoldableCalendar.
    It is overridden because of bug when summary of recurring event stay the same after editing.
    In recurring-ical-events==0.1.20b0 this problem is fixed, but all-day events without timezone lead to exception.
    So i took part of code from 0.1.20b0 but leave 0.1.16b in requirements.
    """

    class RepeatedEvent(UnfoldableCalendar.RepeatedEvent):
        RE_DATETIME_VALUE = re.compile(r"\d+T\d+")

        class Repetition(UnfoldableCalendar.RepeatedEvent.Repetition):
            """
            A repetition of an event. Overridden version of
            recurring_ical_events.UnfoldableCalendar.RepeatedEvent.Repetition. This is overridden to remove the 'RRULE'
            param from ATTRIBUTES_TO_DELETE_ON_COPY, because the 'UNTIL' param must be stored in repetition events to
            calculate its end date.
            """

            ATTRIBUTES_TO_DELETE_ON_COPY = ["RDATE", "EXDATE"]

        def create_rule_with_start(self, rule_string, start):
            """Override to handle issue with non-UTC UNTIL value including time information."""
            try:
                return super().create_rule_with_start(rule_string, start)
            except ValueError:
                # string: FREQ=WEEKLY;UNTIL=20191023T100000;BYDAY=TH;WKST=SU
                # ValueError: RRULE UNTIL values must be specified in UTC when DTSTART is timezone-aware
                # https://stackoverflow.com/a/49991809
                rule_list = rule_string.split(";UNTIL=")
                assert len(rule_list) == 2
                date_end_index = rule_list[1].find(";")
                if date_end_index == -1:
                    date_end_index = len(rule_list[1])
                until_string = rule_list[1][:date_end_index]
                if self.RE_DATETIME_VALUE.match(until_string):
                    rule_string = rule_list[0] + rule_list[1][date_end_index:] + ";UNTIL=" + until_string + "Z"
                    return super().create_rule_with_start(rule_string, self.start)
                # otherwise, keep raising
                raise

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
            if isinstance(recurrence_id, datetime.datetime):
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
                if compare_greater(repetition.start, span_stop) or compare_greater(repetition.start, repetition.stop):
                    # future repetitions could produce invalid events (because of the until rrule)
                    break
                if repetition.is_in_span(span_start, span_stop):
                    add_event(repetition.as_vevent())
        return events


class AmixrRecurringIcalEventsAdapter(IcalService):
    def get_events_from_ical_between(
        self, calendar: Calendar, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> typing.List[Event]:
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
            start_date - datetime.timedelta(days=EXTRA_LOOKUP_DAYS),
            end_date + datetime.timedelta(days=EXTRA_LOOKUP_DAYS),
        )

        def filter_extra_days(event):
            event_start, event_end = self.get_start_and_end_with_respect_to_event_type(event)
            if event_start > event_end:
                return False
            return time_span_contains_event(start_date, end_date, event_start, event_end)

        return list(filter(filter_extra_days, events))

    def get_start_and_end_with_respect_to_event_type(
        self, event: Event
    ) -> typing.Tuple[datetime.datetime, datetime.datetime]:
        """
        Calculate start and end datetime
        """
        from apps.schedules.models import CustomOnCallShift

        start = event[ICAL_DATETIME_START].dt
        end = event[ICAL_DATETIME_END].dt

        match = RE_EVENT_UID_V2.match(event[ICAL_UID]) or RE_EVENT_UID_V1.match(event[ICAL_UID])
        # use different calculation rule for events from custom shifts generated at web
        if match and int(match.groups()[-1]) == CustomOnCallShift.SOURCE_WEB:
            rotation_start = event[ICAL_DATETIME_STAMP].dt
            until_rrule = event.get(ICAL_RRULE, {}).get(ICAL_UNTIL)
            if until_rrule:
                until = until_rrule[0]
                end = min(end, until)

            start = max(start, rotation_start)

        return start, end
