import datetime
import typing

import pytz
from django.utils import timezone


def eta_for_escalation_step_notify_if_time(
    from_time: datetime.time, to_time: datetime.time
) -> typing.Optional[datetime.datetime]:
    """
    Counts eta for STEP_NOTIFY_IF_TIME
    """
    eta: typing.Optional[datetime.datetime] = None

    now = timezone.now()
    current_date = now.date()
    current_time = now.time()

    if from_time < to_time:
        if from_time > current_time:
            eta = datetime.datetime.combine(current_date, from_time).astimezone(pytz.UTC)
        elif current_time >= to_time:
            eta = datetime.datetime.combine((now + datetime.timedelta(days=1)).date(), from_time).astimezone(pytz.UTC)
    elif from_time > to_time:
        if from_time > current_time >= to_time:
            eta = datetime.datetime.combine(current_date, from_time).astimezone(pytz.UTC)
    elif from_time == to_time:
        if from_time > current_time:
            eta = datetime.datetime.combine(current_date, from_time).astimezone(pytz.UTC)
        elif current_time > to_time:
            eta = datetime.datetime.combine((now + datetime.timedelta(days=1)).date(), from_time).astimezone(pytz.UTC)
    return eta
