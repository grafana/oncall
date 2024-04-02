import typing


class GoogleCalendarEventDate(typing.TypedDict):
    # NOTE: in reality I haven't seen this field returned, even despite creating
    # an out of office event with the "All day" checkbox checked. Instead it looks
    # like it just returns the start.dateTime and end.dateTime as midnight of the
    # respective days

    # date: typing.NotRequired[str]
    # """
    # The date, in the format "yyyy-mm-dd", if this is an all-day event.
    # """

    dateTime: typing.NotRequired[str]
    """
    The time, as a combined date-time value (formatted according to RFC3339).
    A time zone offset is required unless a time zone is explicitly specified in timeZone.
    """

    timeZone: typing.NotRequired[str]
    """
    The time zone in which the time is specified. (Formatted as an IANA Time Zone Database name, e.g. "Europe/Zurich".)
    For recurring events this field is required and specifies the time zone in which the recurrence is expanded.
    For single events this field is optional and indicates a custom time zone for the event start/end.
    """


class GoogleCalendarEvent(typing.TypedDict):
    """
    https://developers.google.com/calendar/api/v3/reference/events#resource
    """

    id: str
    """
    Opaque identifier of the event
    """

    start: GoogleCalendarEventDate
    """
    The (inclusive) start time of the event. For a recurring event, this is the start time of the first instance.
    """

    end: GoogleCalendarEventDate
    """
    The (exclusive) end time of the event. For a recurring event, this is the end time of the first instance.
    """

    summary: str
    """
    Title of the event
    """
