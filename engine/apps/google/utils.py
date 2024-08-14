import datetime

from apps.google import constants


def user_granted_all_required_scopes(user_granted_scopes: str) -> bool:
    """
    `user_granted_scopes` should be a space-separated string of scopes
    """
    granted_scopes = user_granted_scopes.split(" ")
    return all(scope in granted_scopes for scope in constants.REQUIRED_OAUTH_SCOPES)


def datetime_strftime(dt: datetime.datetime) -> str:
    return dt.strftime(constants.GOOGLE_CALENDAR_EVENT_DATETIME_FORMAT)


def datetime_strptime(dt: str) -> datetime.datetime:
    return datetime.datetime.strptime(dt, constants.GOOGLE_CALENDAR_EVENT_DATETIME_FORMAT)
