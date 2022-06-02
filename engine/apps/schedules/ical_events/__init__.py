from apps.schedules.ical_events.adapter.amixr_recurring_ical_events_adapter import AmixrRecurringIcalEventsAdapter
from apps.schedules.ical_events.proxy.ical_proxy import IcalProxy

adapter = AmixrRecurringIcalEventsAdapter()
ical_events = IcalProxy(adapter)
