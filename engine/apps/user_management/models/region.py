from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models

from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length


def generate_public_primary_key_for_region():
    prefix = "R"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while Region.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="Region"
        )
        failure_counter += 1

    return new_public_primary_key


class Region(models.Model):
    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_region,
    )

    name = models.CharField(max_length=300)
    slug = models.CharField(max_length=300, unique=True)
    oncall_backend_url = models.URLField()
    is_default = models.BooleanField(default=False)
