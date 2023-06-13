from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Tuple

from icalendar import Calendar, Event


class IcalService(ABC):
    @abstractmethod
    def get_events_from_ical_between(self, calendar: Calendar, start_date: datetime, end_date: datetime) -> List[Event]:
        raise NotImplementedError

    @abstractmethod
    def get_start_and_end_with_respect_to_event_type(self, event: Event) -> Tuple[datetime, datetime]:
        raise NotImplementedError


class IcalProxy(IcalService):
    def __init__(self, ical_adapter: IcalService):
        self.ical_adapter = ical_adapter

    def get_events_from_ical_between(self, calendar: Calendar, start_date: datetime, end_date: datetime) -> List[Event]:
        return self.ical_adapter.get_events_from_ical_between(calendar, start_date, end_date)

    def get_start_and_end_with_respect_to_event_type(self, event: Event) -> Tuple[datetime, datetime]:
        return self.ical_adapter.get_start_and_end_with_respect_to_event_type(event)
