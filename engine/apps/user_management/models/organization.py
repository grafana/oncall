import logging
import typing
import uuid
from urllib.parse import urljoin

from django.apps import apps
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from mirage import fields as mirage_fields

from apps.alerts.models import MaintainableObject
from apps.alerts.tasks import disable_maintenance
from apps.slack.utils import post_message_to_channel
from apps.user_management.subscription_strategy import FreePublicBetaSubscriptionStrategy
from common.insight_log import ChatOpsEvent, ChatOpsType, write_chatops_insight_log
from common.oncall_gateway import create_oncall_connector, delete_oncall_connector, delete_slack_connector
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

logger = logging.getLogger(__name__)


def generate_public_primary_key_for_organization():
    prefix = "O"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while Organization.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="Organization"
        )
        failure_counter += 1

    return new_public_primary_key


class ProvisionedPlugin(typing.TypedDict):
    error: typing.Union[str, None]
    stackId: int
    orgId: int
    onCallToken: str
    license: str


class OrganizationQuerySet(models.QuerySet):
    def create(self, **kwargs):
        instance = super().create(**kwargs)
        if settings.FEATURE_MULTIREGION_ENABLED:
            create_oncall_connector(str(instance.uuid), settings.ONCALL_BACKEND_REGION)
        return instance

    def delete(self):
        # Be careful with deleting via queryset - it doesn't delete chatops-proxy connectors.
        self.update(deleted_at=timezone.now())

    def hard_delete(self):
        super().delete()


class OrganizationManager(models.Manager):
    def get_queryset(self):
        return OrganizationQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class Organization(MaintainableObject):

    objects = OrganizationManager()
    objects_with_deleted = models.Manager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscription_strategy = self._get_subscription_strategy()

    def delete(self):
        if settings.FEATURE_MULTIREGION_ENABLED:
            delete_oncall_connector(str(self.uuid))
            if self.slack_team_identity:
                delete_slack_connector(str(self.uuid))
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self):
        super().delete()

    def _get_subscription_strategy(self):
        if self.pricing_version == self.FREE_PUBLIC_BETA_PRICING:
            return FreePublicBetaSubscriptionStrategy(self)

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_organization,
    )

    stack_id = models.PositiveIntegerField()
    org_id = models.PositiveIntegerField()

    stack_slug = models.CharField(max_length=300)
    org_slug = models.CharField(max_length=300)
    org_title = models.CharField(max_length=300)
    region_slug = models.CharField(max_length=300, null=True, default=None)
    migration_destination = models.ForeignKey(
        to="user_management.Region",
        to_field="slug",
        db_column="migration_destination_slug",
        on_delete=models.SET_NULL,
        related_name="regions",
        default=None,
        null=True,
    )
    cluster_slug = models.CharField(max_length=300, null=True, default=None)

    grafana_url = models.URLField()

    api_token = mirage_fields.EncryptedCharField(max_length=300)

    (
        API_TOKEN_STATUS_PENDING,
        API_TOKEN_STATUS_OK,
        API_TOKEN_STATUS_FAILED,
    ) = range(3)
    API_TOKEN_STATUS_CHOICES = (
        (API_TOKEN_STATUS_PENDING, "API Token Status Pending"),
        (API_TOKEN_STATUS_OK, "API Token Status Ok"),
        (API_TOKEN_STATUS_FAILED, "API Token Status Failed"),
    )
    api_token_status = models.IntegerField(
        choices=API_TOKEN_STATUS_CHOICES,
        default=API_TOKEN_STATUS_PENDING,
    )

    gcom_token = mirage_fields.EncryptedCharField(max_length=300, null=True, default=None)
    gcom_token_org_last_time_synced = models.DateTimeField(null=True, default=None)

    last_time_synced = models.DateTimeField(null=True, default=None)

    is_resolution_note_required = models.BooleanField(default=False)

    archive_alerts_from = models.DateField(default="1970-01-01")

    # TODO: this field is specific to slack and will be moved to a different model
    slack_team_identity = models.ForeignKey(
        "slack.SlackTeamIdentity", on_delete=models.PROTECT, null=True, default=None, related_name="organizations"
    )

    # Slack specific field with general log channel id
    general_log_channel_id = models.CharField(max_length=100, null=True, default=None)

    # uuid used to unuqie identify organization in different clusters
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    deleted_at = models.DateTimeField(null=True)

    # Organization Settings configured from slack
    (
        ACKNOWLEDGE_REMIND_NEVER,
        ACKNOWLEDGE_REMIND_1H,
        ACKNOWLEDGE_REMIND_3H,
        ACKNOWLEDGE_REMIND_5H,
        ACKNOWLEDGE_REMIND_10H,
    ) = range(5)
    ACKNOWLEDGE_REMIND_CHOICES = (
        (ACKNOWLEDGE_REMIND_NEVER, "Never remind about ack-ed incidents"),
        (ACKNOWLEDGE_REMIND_1H, "Remind every 1 hour"),
        (ACKNOWLEDGE_REMIND_3H, "Remind every 3 hours"),
        (ACKNOWLEDGE_REMIND_5H, "Remind every 5 hours"),
        (ACKNOWLEDGE_REMIND_10H, "Remind every 10 hours"),
    )
    ACKNOWLEDGE_REMIND_DELAY = {
        ACKNOWLEDGE_REMIND_NEVER: 0,
        ACKNOWLEDGE_REMIND_1H: 3600,
        ACKNOWLEDGE_REMIND_3H: 10800,
        ACKNOWLEDGE_REMIND_5H: 18000,
        ACKNOWLEDGE_REMIND_10H: 36000,
    }
    acknowledge_remind_timeout = models.IntegerField(
        choices=ACKNOWLEDGE_REMIND_CHOICES,
        default=ACKNOWLEDGE_REMIND_NEVER,
    )

    (
        UNACKNOWLEDGE_TIMEOUT_NEVER,
        UNACKNOWLEDGE_TIMEOUT_5MIN,
        UNACKNOWLEDGE_TIMEOUT_15MIN,
        UNACKNOWLEDGE_TIMEOUT_30MIN,
        UNACKNOWLEDGE_TIMEOUT_45MIN,
    ) = range(5)

    UNACKNOWLEDGE_TIMEOUT_CHOICES = (
        (UNACKNOWLEDGE_TIMEOUT_NEVER, "and never unack"),
        (UNACKNOWLEDGE_TIMEOUT_5MIN, "and unack in 5 min if no response"),
        (UNACKNOWLEDGE_TIMEOUT_15MIN, "and unack in 15 min if no response"),
        (UNACKNOWLEDGE_TIMEOUT_30MIN, "and unack in 30 min if no response"),
        (UNACKNOWLEDGE_TIMEOUT_45MIN, "and unack in 45 min if no response"),
    )
    UNACKNOWLEDGE_TIMEOUT_DELAY = {
        UNACKNOWLEDGE_TIMEOUT_NEVER: 0,
        UNACKNOWLEDGE_TIMEOUT_5MIN: 300,
        UNACKNOWLEDGE_TIMEOUT_15MIN: 900,
        UNACKNOWLEDGE_TIMEOUT_30MIN: 1800,
        UNACKNOWLEDGE_TIMEOUT_45MIN: 2700,
    }
    unacknowledge_timeout = models.IntegerField(
        choices=UNACKNOWLEDGE_TIMEOUT_CHOICES,
        default=UNACKNOWLEDGE_TIMEOUT_NEVER,
    )

    # This field is used to calculate public suggestions time
    # Not sure if it is needed
    datetime = models.DateTimeField(auto_now_add=True)

    FREE_PUBLIC_BETA_PRICING = 0
    PRICING_CHOICES = ((FREE_PUBLIC_BETA_PRICING, "Free public beta"),)
    pricing_version = models.PositiveIntegerField(choices=PRICING_CHOICES, default=FREE_PUBLIC_BETA_PRICING)

    is_amixr_migration_started = models.BooleanField(default=False)
    is_rbac_permissions_enabled = models.BooleanField(default=False)
    is_grafana_incident_enabled = models.BooleanField(default=False)

    class Meta:
        unique_together = ("stack_id", "org_id")

    def provision_plugin(self) -> ProvisionedPlugin:
        PluginAuthToken = apps.get_model("auth_token", "PluginAuthToken")
        _, token = PluginAuthToken.create_auth_token(organization=self)
        return {
            "stackId": self.stack_id,
            "orgId": self.org_id,
            "onCallToken": token,
            "license": settings.LICENSE,
        }

    def revoke_plugin(self):
        token_model = apps.get_model("auth_token", "PluginAuthToken")
        token_model.objects.filter(organization=self).delete()

    """
    Following methods: start_disable_maintenance_task, force_disable_maintenance, get_organization, get_verbal serve for
    MaintainableObject.
    """

    def start_disable_maintenance_task(self, countdown):
        maintenance_uuid = disable_maintenance.apply_async(
            args=(),
            kwargs={
                "organization_id": self.pk,
            },
            countdown=countdown,
        )
        return maintenance_uuid

    def force_disable_maintenance(self, user):
        disable_maintenance(organization_id=self.pk, force=True, user_id=user.pk)

    def get_organization(self):
        return self

    def get_team(self):
        return None

    def get_verbal(self):
        return self.org_title

    def notify_about_maintenance_action(self, text, send_to_general_log_channel=True):
        # TODO: this method should be refactored.
        # It's binded to slack and sending maintenance notification only there.
        if send_to_general_log_channel:
            post_message_to_channel(self, self.general_log_channel_id, text)

    """
    Following methods:
    phone_calls_left, sms_left, emails_left, notifications_limit_web_report
    serve for calculating notifications' limits and composed from self.subscription_strategy.
    """

    def phone_calls_left(self, user):
        return self.subscription_strategy.phone_calls_left(user)

    def sms_left(self, user):
        return self.subscription_strategy.sms_left(user)

    # todo: manage backend specific limits in messaging backend
    def emails_left(self, user):
        return self.subscription_strategy.emails_left(user)

    def notifications_limit_web_report(self, user):
        return self.subscription_strategy.notifications_limit_web_report(user)

    def set_general_log_channel(self, channel_id, channel_name, user):
        if self.general_log_channel_id != channel_id:
            old_general_log_channel_id = self.slack_team_identity.cached_channels.filter(
                slack_id=self.general_log_channel_id
            ).first()
            old_channel_name = old_general_log_channel_id.name if old_general_log_channel_id else None
            self.general_log_channel_id = channel_id
            self.save(update_fields=["general_log_channel_id"])
            write_chatops_insight_log(
                author=user,
                event_name=ChatOpsEvent.DEFAULT_CHANNEL_CHANGED,
                chatops_type=ChatOpsType.SLACK,
                prev_channel=old_channel_name,
                new_channel=channel_name,
            )

    @property
    def web_link(self):
        return urljoin(self.grafana_url, "a/grafana-oncall-app/")

    @property
    def web_link_with_uuid(self):
        # It's a workaround to pass some unique identifier to the oncall gateway while proxying telegram requests
        return urljoin(self.grafana_url, f"a/grafana-oncall-app/?oncall-uuid={self.uuid}")

    def __str__(self):
        return f"{self.pk}: {self.org_title}"

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "organization"

    @property
    def insight_logs_verbal(self):
        return self.org_title

    @property
    def insight_logs_serialized(self):
        return {
            "name": self.org_title,
            "is_resolution_note_required": self.is_resolution_note_required,
            "archive_alerts_from": self.archive_alerts_from.isoformat(),
        }

    @property
    def insight_logs_metadata(self):
        return {}

    @property
    def is_moved(self):
        return self.migration_destination_id is not None
