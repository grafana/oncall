import datetime
import typing

from icalendar import Calendar, Event
from recurring_ical_events import UnfoldableCalendar, time_span_contains_event

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
        events = UnfoldableCalendar(calendar).between(
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
