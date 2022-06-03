from datetime import datetime
from typing import List

import recurring_ical_events
from icalendar import Calendar, Event

from apps.schedules.ical_events.proxy.ical_proxy import IcalService


class RecurringIcalEventsAdapter(IcalService):
    """
    Adapter of pure recurring_ical_events library as it was used before implementing Ical Adapters.
    Not recommended for use.
    """

    def get_events_from_ical_between(self, calendar: Calendar, start_date: datetime, end_date: datetime) -> List[Event]:
        return recurring_ical_events.of(calendar).between(start_date, end_date)
