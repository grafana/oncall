import json
import os
import typing
from dataclasses import dataclass


@dataclass
class CustomRateLimit:
    integration: str
    organization: str
    public_api: str


def getenv_custom_ratelimit(variable_name: str, default: dict) -> typing.Dict[str, CustomRateLimit]:
    custom_ratelimits_str = os.environ.get(variable_name)
    if custom_ratelimits_str is None:
        return default
    value = load_custom_ratelimits(custom_ratelimits_str)
    return value


def load_custom_ratelimits(custom_ratelimits_str: str) -> typing.Dict[str, CustomRateLimit]:
    custom_ratelimits_dict = json.loads(custom_ratelimits_str)
    # Convert the parsed JSON into a dictionary of RateLimit dataclasses
    custom_ratelimits = {key: CustomRateLimit(**value) for key, value in custom_ratelimits_dict.items()}

    return custom_ratelimits
