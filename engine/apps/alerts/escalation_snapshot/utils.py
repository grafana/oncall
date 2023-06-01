import pytz_deprecation_shim as pytz
from django.utils import timezone


def eta_for_escalation_step_notify_if_time(from_time, to_time, current_time=None) -> timezone.datetime:
    """
    Counts eta for STEP_NOTIFY_IF_TIME
    :return: timezone.datetime
    """
    eta = current_time
    current_time = current_time or timezone.now()
    if from_time < to_time:
        if from_time > current_time.time():
            eta = timezone.datetime.combine(current_time.date(), from_time).astimezone(pytz.UTC)
        elif current_time.time() >= to_time:
            eta = timezone.datetime.combine((current_time + timezone.timedelta(days=1)).date(), from_time).astimezone(
                pytz.UTC
            )
    elif from_time > to_time:
        if from_time > current_time.time() >= to_time:
            eta = timezone.datetime.combine(current_time.date(), from_time).astimezone(pytz.UTC)
    elif from_time == to_time:
        if from_time > current_time.time():
            eta = timezone.datetime.combine(current_time.date(), from_time).astimezone(pytz.UTC)
        elif current_time.time() > to_time:
            eta = timezone.datetime.combine((current_time + timezone.timedelta(days=1)).date(), from_time).astimezone(
                pytz.UTC
            )
    return eta
