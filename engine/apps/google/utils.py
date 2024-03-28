import datetime

from apps.google import constants


def datetime_strftime(dt: datetime.datetime) -> str:
    return dt.strftime(constants.GOOGLE_CALENDAR_EVENT_DATETIME_FORMAT)


def datetime_strptime(dt: str) -> datetime.datetime:
    return datetime.datetime.strptime(dt, constants.GOOGLE_CALENDAR_EVENT_DATETIME_FORMAT)
