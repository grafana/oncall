import random

from django.conf import settings


class UseRandomReadonlyDbManagerMixin:
    """
    Use this Mixin in ModelManagers, when you want to use the random readonly replica
    """

    @property
    def using_readonly_db(self):
        """Select one of the readonly databases this QuerySet should execute against."""
        if hasattr(settings, "READONLY_DATABASES") and len(settings.READONLY_DATABASES) > 0:
            using_db = random.choice(list(settings.READONLY_DATABASES.keys()))
            return self.using(using_db)
        else:
            # Use "default" database
            # Django uses the database with the alias of default when no other database has been selected.
            # https://docs.djangoproject.com/en/3.2/topics/db/multi-db/#defining-your-databases
            return self.using("default")
