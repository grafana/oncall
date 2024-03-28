import typing

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import F
from django.utils import timezone

from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import EscalationPolicy


def generate_public_primary_key_for_custom_button():
    prefix = "K"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while CustomButton.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="CustomButton"
        )
        failure_counter += 1

    return new_public_primary_key


class CustomButtonQueryset(models.QuerySet):
    def delete(self):
        self.update(deleted_at=timezone.now(), name=F("name") + "_deleted_" + F("public_primary_key"))


class CustomButtonManager(models.Manager):
    def get_queryset(self):
        return CustomButtonQueryset(self.model, using=self._db).filter(deleted_at=None)


class CustomButton(models.Model):
    escalation_policies: "RelatedManager['EscalationPolicy']"

    objects = CustomButtonManager()

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_custom_button,
    )

    organization = models.ForeignKey(
        "user_management.Organization", on_delete=models.CASCADE, related_name="custom_buttons"
    )
    team = models.ForeignKey(
        "user_management.Team",
        on_delete=models.SET_NULL,
        related_name="custom_buttons",
        null=True,
        default=None,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    webhook = models.CharField(max_length=1000, null=True, default=None)
    data = models.TextField(null=True, default=None)
    user = models.CharField(max_length=100, null=True, default=None)
    password = models.CharField(max_length=100, null=True, default=None)
    deleted_at = models.DateTimeField(blank=True, null=True)
    authorization_header = models.CharField(max_length=1000, null=True, default=None)
    forward_whole_payload = models.BooleanField(default=False)

    class Meta:
        unique_together = ("name", "organization")

    def __str__(self):
        return str(self.name)
