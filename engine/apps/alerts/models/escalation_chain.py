import typing

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models, transaction

from apps.alerts.models.escalation_policy import generate_public_primary_key_for_escalation_policy
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import ChannelFilter, EscalationPolicy


def generate_public_primary_key_for_escalation_chain():
    prefix = "F"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while EscalationChain.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="EscalationChain"
        )
        failure_counter += 1

    return new_public_primary_key


class EscalationChain(models.Model):
    channel_filters: "RelatedManager['ChannelFilter']"
    escalation_policies: "RelatedManager['EscalationPolicy']"

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_escalation_chain,
    )

    organization = models.ForeignKey(
        "user_management.Organization", on_delete=models.CASCADE, related_name="escalation_chains"
    )
    team = models.ForeignKey(
        "user_management.Team",
        on_delete=models.SET_NULL,
        related_name="escalation_chains",
        null=True,
        default=None,
    )
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("organization", "name")

    def __str__(self):
        return f"{self.pk}: {self.name}"

    def make_copy(self, copy_name: str, team):
        with transaction.atomic():
            copied_chain = EscalationChain.objects.create(
                organization=self.organization,
                team=team,
                name=copy_name,
            )
            for escalation_policy in self.escalation_policies.all():
                # https://docs.djangoproject.com/en/3.2/topics/db/queries/#copying-model-instances
                notify_to_users_queue = escalation_policy.notify_to_users_queue.all()

                escalation_policy.pk = None
                escalation_policy.public_primary_key = generate_public_primary_key_for_escalation_policy()
                escalation_policy.last_notified_user = None
                escalation_policy.escalation_chain = copied_chain
                escalation_policy.save()
                escalation_policy.notify_to_users_queue.set(notify_to_users_queue)
            return copied_chain

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "escalation_chain"

    @property
    def insight_logs_verbal(self):
        return self.name

    @property
    def insight_logs_serialized(self):
        result = {
            "name": self.name,
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
