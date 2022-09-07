import re

ICAL_DATETIME_START = "DTSTART"
ICAL_DATETIME_END = "DTEND"
ICAL_DATETIME_STAMP = "DTSTAMP"
ICAL_SUMMARY = "SUMMARY"
ICAL_DESCRIPTION = "DESCRIPTION"
ICAL_ATTENDEE = "ATTENDEE"
ICAL_UID = "UID"
ICAL_RRULE = "RRULE"
ICAL_UNTIL = "UNTIL"
RE_PRIORITY = re.compile(r"^\[L(\d)\]")
RE_EVENT_UID_V1 = re.compile(r"amixr-([\w\d-]+)-U(\d+)-E(\d+)-S(\d+)")
RE_EVENT_UID_V2 = re.compile(r"oncall-([\w\d-]+)-PK([\w\d]+)-U(\d+)-E(\d+)-S(\d+)")
