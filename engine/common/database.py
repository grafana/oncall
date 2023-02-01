import random

from django.conf import settings


def get_random_readonly_database_key_if_present_otherwise_default() -> str:
    """
    This function returns a string, representing a key in the DATABASES django settings.
    If settings.READONLY_DATABASES is set, and non-empty, it randomly chooses one of the read-only databases,
    otherwise it falls back to "default".

    This is primarily intended to be used for django's QuerySet.using() function
    """
    using_db = "default"
    if hasattr(settings, "READONLY_DATABASES") and len(settings.READONLY_DATABASES) > 0:
        using_db = random.choice(list(settings.READONLY_DATABASES.keys()))
    return using_db
