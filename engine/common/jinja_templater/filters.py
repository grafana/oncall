import json
import re

from django.utils.dateparse import parse_datetime


def datetimeformat(value, format="%H:%M / %d-%m-%Y"):
    try:
        return value.strftime(format)
    except AttributeError:
        return None


def iso8601_to_time(value):
    try:
        return parse_datetime(value)
    except (ValueError, AttributeError, TypeError):
        return None


def to_pretty_json(value):
    try:
        return json.dumps(value, sort_keys=True, indent=4, separators=(",", ": "), ensure_ascii=False)
    except (ValueError, AttributeError, TypeError):
        return None


def regex_replace(value, find, replace):
    try:
        return re.sub(find, replace, value)
    except (ValueError, AttributeError, TypeError):
        return None


def regex_match(pattern, value):
    try:
        return bool(re.match(value, pattern))
    except (ValueError, AttributeError, TypeError):
        return None


def regex_search(pattern, value):
    try:
        return bool(re.search(value, pattern))
    except (ValueError, AttributeError, TypeError):
        return None


def json_dumps(value):
    try:
        return json.dumps(value)
    except (ValueError, AttributeError, TypeError):
        return None
