from dataclasses import dataclass


@dataclass
class CustomRateLimit:
    integration: str
    organization: str
    public_api: str
