from django.apps import AppConfig
from django.db import models


# enable a __lower field lookup for email fields
# https://docs.djangoproject.com/en/4.1/howto/custom-lookups/#a-bilateral-transformer-example
class LowerCase(models.Transform):
    lookup_name = "lower"
    function = "LOWER"


class UserManagementConfig(AppConfig):
    name = "apps.user_management"

    def ready(self):
        models.EmailField.register_lookup(LowerCase)
