from typing import Callable, Optional, TypeVar

from migrator.config import ONCALL_DELAY_OPTIONS

T = TypeVar("T")


def find(
    lst: list[T], cond: Callable[[T], bool], reverse: bool = False
) -> Optional[int]:
    indices = range(len(lst))

    if reverse:
        indices = indices[::-1]

    for idx in indices:
        if cond(lst[idx]):
            return idx

    return None


def split(lst: list[T], cond: Callable[[T], bool]) -> list[list[T]]:
    idx = find(lst, cond)

    if idx is None:
        return [lst]

    return [lst[: idx + 1]] + split(lst[idx + 1 :], cond)


def remove_duplicates(
    lst: list[T],
    split_condition: Callable[[T], bool],
    duplicate_condition: Callable[[T], bool],
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


def find_by_id(resources: list[dict], resource_id: str) -> Optional[dict]:
    for resource in resources:
        if resource["id"] == resource_id:
            return resource

    return None


def find_closest_value(lst: list[int], value: int) -> int:
    return min(lst, key=lambda v: abs(v - value))


def transform_wait_delay(delay: int) -> int:
    return find_closest_value(ONCALL_DELAY_OPTIONS, delay) * 60
