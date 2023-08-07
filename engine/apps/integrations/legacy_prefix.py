"""
legacy_prefix.py provides utils to work with legacy integration types, which are prefixed with 'legacy_'.
"""

legacy_prefix = "legacy_"


def has_legacy_prefix(integration_type: str) -> bool:
    return integration_type.startswith(legacy_prefix)


def remove_legacy_prefix(integration_type: str) -> str:
    return integration_type.removeprefix(legacy_prefix)
