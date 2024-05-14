import datetime
import typing

from lib.base_config import ONCALL_DELAY_OPTIONS

T = typing.TypeVar("T")


def find(
    lst: list[T], cond: typing.Callable[[T], bool], reverse: bool = False
) -> typing.Optional[int]:
    indices = range(len(lst))

    if reverse:
        indices = indices[::-1]

    for idx in indices:
        if cond(lst[idx]):
            return idx

    return None


def split(lst: list[T], cond: typing.Callable[[T], bool]) -> list[list[T]]:
    idx = find(lst, cond)

    if idx is None:
        return [lst]

    return [lst[: idx + 1]] + split(lst[idx + 1 :], cond)


def remove_duplicates(
    lst: list[T],
    split_condition: typing.Callable[[T], bool],
    duplicate_condition: typing.Callable[[T], bool],
) -> list[T]:
    result = []
    chunks = split(lst, split_condition)

    for chunk in chunks:
        count = len([element for element in chunk if duplicate_condition(element)])
        if count > 1:
            for _ in range(count - 1):
                idx = find(chunk, duplicate_condition, reverse=True)
                del chunk[idx]

        result += chunk

    return result


def find_by_id(
    objects: typing.List[T], value: typing.Any, key="id"
) -> typing.Optional[T]:
    """
    Allows finding an object in a list of objects.

    Returns the first object whose value for `key` matches the given `value`. Supports
    nested keys by using '.' as a separator.
    """

    for obj in objects:
        # Split the key by '.' to handle nested keys
        keys = key.split(".")
        # Initialize current_value to the current object
        current_value = obj

        # Iterate through the keys to access nested values
        for k in keys:
            # If the current value is a dictionary and the key exists, update current_value
            if isinstance(current_value, dict) and k in current_value:
                current_value = current_value[k]
            # If the current value is a list, search each element for the key
            elif isinstance(current_value, list):
                nested_objs = [
                    item[k]
                    for item in current_value
                    if isinstance(item, dict) and k in item
                ]
                if nested_objs:
                    current_value = nested_objs[0]
                else:
                    current_value = None
            # If the key doesn't exist or the current value is not a dictionary, break the loop
            else:
                current_value = None
                break

        # If the current value matches the given value, return the object
        if current_value == value:
            return obj

    # If no object matches, return None
    return None


def find_closest_value(lst: list[int], value: int) -> int:
    return min(lst, key=lambda v: abs(v - value))


def transform_wait_delay(delay: int) -> int:
    return find_closest_value(ONCALL_DELAY_OPTIONS, delay) * 60


def duration_to_frequency_and_interval(duration: datetime.timedelta) -> tuple[str, int]:
    """
    Convert a duration to shift frequency and interval.
    For example, 1 day duration returns ("daily", 1), 14 days returns ("weekly", 2),
    """
    seconds = int(duration.total_seconds())

    assert seconds >= 3600, "Rotation must be at least 1 hour"
    hours = seconds // 3600

    if hours >= 24 and hours % 24 == 0:
        days = hours // 24
        if days >= 7 and days % 7 == 0:
            weeks = days // 7
            return "weekly", weeks
        else:
            return "daily", days
    else:
        return "hourly", hours


def dt_to_oncall_datetime(dt: datetime.datetime) -> str:
    """
    Convert a datetime object to an OnCall datetime string.
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%S")
