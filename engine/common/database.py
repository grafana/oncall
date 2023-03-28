import random

from django.conf import settings
from django.db import models


def get_random_readonly_database_key_if_present_otherwise_default() -> str:
    """
    This function returns a string, representing a key in the `DATABASES` django settings.
    If `settings.READONLY_DATABASES` is set, and non-empty, it randomly chooses one of the read-only databases,
    otherwise it falls back to "default".

    This is primarily intended to be used for django's `QuerySet.using()` function
    """
    using_db = "default"
    if hasattr(settings, "READONLY_DATABASES") and len(settings.READONLY_DATABASES) > 0:
        using_db = random.choice(list(settings.READONLY_DATABASES.keys()))
    return using_db


def NON_POLYMORPHIC_SET_NULL(collector, field, sub_objs, using):
    """
    django-polymorphic has a bug where it doesn't properly handle the `on_delete` argument:
    https://github.com/django-polymorphic/django-polymorphic/issues/229#issuecomment-398434412.
    This is a workaround that uses the same code as the original `SET_NULL` function, but with the
    `non_polymorphic()` function applied to the `sub_objs` queryset.
    """
    return models.SET_NULL(collector, field, sub_objs.non_polymorphic(), using)


def NON_POLYMORPHIC_CASCADE(collector, field, sub_objs, using):
    """
    django-polymorphic has a bug where it doesn't properly handle the `on_delete` argument:
    https://github.com/django-polymorphic/django-polymorphic/issues/229#issuecomment-398434412.
    This is a workaround that uses the same code as the original `CASCADE` function, but with the
    `non_polymorphic()` function applied to the `sub_objs` queryset.
    """
    return models.CASCADE(collector, field, sub_objs.non_polymorphic(), using)
