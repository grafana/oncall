import json
import logging
import re
import typing
from json import JSONDecodeError

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import F
from django.utils import timezone
from requests.auth import HTTPBasicAuth

from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import EscalationPolicy


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class CustomButton(models.Model):
    escalation_policies: "RelatedManager['EscalationPolicy']"

    objects = CustomButtonManager()
    objects_with_deleted = models.Manager()

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

    def delete(self):
        logger.info(f"Soft delete of custom button {self}")
        self.escalation_policies.all().delete()
        self.deleted_at = timezone.now()
        # 100 - 22 = 78. 100 is max len of name field, and 22 is len of suffix _deleted_<public_primary_key>
        # So for case when user created button with maximum length name it is needed to trim it to 78 chars to be
        # able to add suffix.
        self.name = f"{self.name[:78]}_deleted_{self.public_primary_key}"
        self.save()

    def hard_delete(self):
        super().delete()

    def build_post_kwargs(self, alert):
        post_kwargs = {}
        if self.user and self.password:
            post_kwargs["auth"] = HTTPBasicAuth(self.user, self.password)
        if self.authorization_header:
            post_kwargs["headers"] = {"Authorization": self.authorization_header}
        if self.forward_whole_payload:
            post_kwargs["json"] = alert.raw_request_data
        elif self.data:
            try:
                rendered_data = apply_jinja_template(
                    self.data,
                    alert_payload=self._escape_alert_payload(alert.raw_request_data),
                    alert_group_id=alert.group.public_primary_key,
                )
                try:
                    post_kwargs["json"] = json.loads(rendered_data)
                except JSONDecodeError:
                    post_kwargs["data"] = rendered_data
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                post_kwargs["json"] = {"error": e.fallback_message}
        return post_kwargs

    def _escape_alert_payload(self, payload: dict):
        if isinstance(payload, dict):
            escaped_data = EscapeDoubleQuotesDict()
            for key in payload.keys():
                escaped_data[key] = self._escape_alert_payload(payload[key])
        elif isinstance(payload, list):
            escaped_data = []
            for value in payload:
                escaped_data.append(self._escape_alert_payload(value))
        elif isinstance(payload, str):
            escaped_data = self._escape_string(payload)
        else:
            escaped_data = payload
        return escaped_data

    def _escape_string(self, string: str):
        """
        Escapes string to use in json.loads() method.
        json.dumps is the simples way to escape all special characters in string.
        First and last chars are quotes from json.dumps(), we don't need them, only escaping.
        """
        return json.dumps(string)[1:-1]

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "outgoing_webhook"

    @property
    def insight_logs_verbal(self):
        return self.name

    @property
    def insight_logs_serialized(self):
        result = {
            "name": self.name,
            "webhook": self.webhook,
            "user": self.user,
            "password": self.password,
            "authorization_header": self.authorization_header,
            "data": self.data,
            "forward_whole_payload": self.forward_whole_payload,
        }

        if self.team:
            result["team"] = self.team.name
            result["team_id"] = self.team.public_primary_key
        else:
            result["team"] = "General"
        return result

    @property
    def insight_logs_metadata(self):
        result = {}
        if self.team:
            result["team"] = self.team.name
            result["team_id"] = self.team.public_primary_key
        else:
            result["team"] = "General"
        return result


class EscapeDoubleQuotesDict(dict):
    """
    Warning: Please, do not use this dict anywhere except CustomButton._escape_alert_payload.
    This custom dict escapes double quotes to produce string which is safe to pass to json.loads()
    It fixes case when CustomButton.build_post_kwargs failing on payloads which contains string with single quote.
    In this case built-in dict's str method will surround value with double quotes.

    For example:

    alert_payload = {
        "text": "Hi, it's alert",
    }
    template = '{"data" : "{{ alert_payload }}"}'
    rendered = '{"data" : "{\'text\': "Hi, it\'s alert"}"}'
    # and json.loads(rendered) will fail due to unescaped double quotes

    # Now with EscapeDoubleQuotesDict.

    alert_payload = EscapeDoubleQuotesDict({
        "text": "Hi, it's alert",
    })
    rendered = '{"data" : "{\'text\': \\"Hi, it\'s alert\\"}"}'
    # and json.loads(rendered) works.
    """

    def __str__(self):
        original_str = super().__str__()
        if '"' in original_str:
            return re.sub('(?<!\\\\)"', '\\\\"', original_str)
        return original_str
