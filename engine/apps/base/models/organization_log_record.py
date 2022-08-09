import logging

from django.apps import apps
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import JSONField
from emoji import emojize

from apps.alerts.models.maintainable_object import MaintainableObject
from apps.user_management.organization_log_creator import OrganizationLogType
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

insight_logger = logging.getLogger("insight_logger")


def generate_public_primary_key_for_organization_log():
    prefix = "V"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while OrganizationLogRecord.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="OrganizationLogRecord"
        )
        failure_counter += 1

    return new_public_primary_key


class OrganizationLogRecordManager(models.Manager):
    def create(self, organization, author, type, description):
        # set labels
        labels = OrganizationLogRecord.LABELS_FOR_TYPE[type]
        return super().create(
            organization=organization,
            author=author,
            description=description,
            _labels=labels,
        )


class OrganizationLogRecord(models.Model):

    objects = OrganizationLogRecordManager()

    LABEL_ORGANIZATION = "organization"
    LABEL_SLACK = "slack"
    LABEL_TELEGRAM = "telegram"
    LABEL_DEFAULT_CHANNEL = "default channel"
    LABEL_SLACK_WORKSPACE_CONNECTED = "slack workspace connected"
    LABEL_SLACK_WORKSPACE_DISCONNECTED = "slack workspace disconnected"
    LABEL_TELEGRAM_CHANNEL_CONNECTED = "telegram channel connected"
    LABEL_TELEGRAM_CHANNEL_DISCONNECTED = "telegram channel disconnected"
    LABEL_INTEGRATION = "integration"
    LABEL_INTEGRATION_CREATED = "integration created"
    LABEL_INTEGRATION_DELETED = "integration deleted"
    LABEL_INTEGRATION_CHANGED = "integration changed"
    LABEL_INTEGRATION_HEARTBEAT = "integration heartbeat"
    LABEL_INTEGRATION_HEARTBEAT_CREATED = "integration heartbeat created"
    LABEL_INTEGRATION_HEARTBEAT_CHANGED = "integration heartbeat changed"
    LABEL_MAINTENANCE = "maintenance"
    LABEL_MAINTENANCE_STARTED = "maintenance started"
    LABEL_MAINTENANCE_STOPPED = "maintenance stopped"
    LABEL_DEBUG = "debug"
    LABEL_DEBUG_STARTED = "debug started"
    LABEL_DEBUG_STOPPED = "debug stopped"
    LABEL_CHANNEL_FILTER = "route"
    LABEL_CHANNEL_FILTER_CREATED = "route created"
    LABEL_CHANNEL_FILTER_CHANGED = "route changed"
    LABEL_CHANNEL_FILTER_DELETED = "route deleted"
    LABEL_ESCALATION_CHAIN = "escalation chain"
    LABEL_ESCALATION_CHAIN_CREATED = "escalation chain created"
    LABEL_ESCALATION_CHAIN_DELETED = "escalation chain deleted"
    LABEL_ESCALATION_CHAIN_CHANGED = "escalation chain changed"
    LABEL_ESCALATION_POLICY = "escalation policy"
    LABEL_ESCALATION_POLICY_CREATED = "escalation policy created"
    LABEL_ESCALATION_POLICY_DELETED = "escalation policy deleted"
    LABEL_ESCALATION_POLICY_CHANGED = "escalation policy changed"
    LABEL_CUSTOM_ACTION = "custom action"
    LABEL_CUSTOM_ACTION_CREATED = "custom action created"
    LABEL_CUSTOM_ACTION_DELETED = "custom action deleted"
    LABEL_CUSTOM_ACTION_CHANGED = "custom action changed"
    LABEL_SCHEDULE = "schedule"
    LABEL_SCHEDULE_CREATED = "schedule created"
    LABEL_SCHEDULE_DELETED = "schedule deleted"
    LABEL_SCHEDULE_CHANGED = "schedule changed"
    LABEL_ON_CALL_SHIFT = "on-call shift"
    LABEL_ON_CALL_SHIFT_CREATED = "on-call shift created"
    LABEL_ON_CALL_SHIFT_DELETED = "on-call shift deleted"
    LABEL_ON_CALL_SHIFT_CHANGED = "on-call shift changed"
    LABEL_USER = "user"
    LABEL_USER_CREATED = "user created"
    LABEL_USER_SETTINGS_CHANGED = "user changed"
    LABEL_ORGANIZATION_SETTINGS_CHANGED = "organization settings changed"
    LABEL_TELEGRAM_TO_USER_CONNECTED = "telegram to user connected"
    LABEL_TELEGRAM_FROM_USER_DISCONNECTED = "telegram from user disconnected"
    LABEL_API_TOKEN = "api token"
    LABEL_API_TOKEN_CREATED = "api token created"
    LABEL_API_TOKEN_REVOKED = "api token revoked"
    LABEL_ESCALATION_CHAIN_COPIED = "escalation chain copied"
    LABEL_SCHEDULE_EXPORT_TOKEN = "schedule export token"
    LABEL_SCHEDULE_EXPORT_TOKEN_CREATED = "schedule export token created"
    LABEL_MESSAGING_BACKEND_CHANNEL_CHANGED = "messaging backend channel changed"
    LABEL_MESSAGING_BACKEND_CHANNEL_DELETED = "messaging backend channel deleted"
    LABEL_MESSAGING_BACKEND_USER_DISCONNECTED = "messaging backend user disconnected"

    LABELS = [
        LABEL_ORGANIZATION,
        LABEL_SLACK,
        LABEL_TELEGRAM,
        LABEL_DEFAULT_CHANNEL,
        LABEL_SLACK_WORKSPACE_CONNECTED,
        LABEL_SLACK_WORKSPACE_DISCONNECTED,
        LABEL_TELEGRAM_CHANNEL_CONNECTED,
        LABEL_TELEGRAM_CHANNEL_DISCONNECTED,
        LABEL_INTEGRATION,
        LABEL_INTEGRATION_CREATED,
        LABEL_INTEGRATION_DELETED,
        LABEL_INTEGRATION_CHANGED,
        LABEL_INTEGRATION_HEARTBEAT,
        LABEL_INTEGRATION_HEARTBEAT_CREATED,
        LABEL_INTEGRATION_HEARTBEAT_CHANGED,
        LABEL_MAINTENANCE,
        LABEL_MAINTENANCE_STARTED,
        LABEL_MAINTENANCE_STOPPED,
        LABEL_DEBUG,
        LABEL_DEBUG_STARTED,
        LABEL_DEBUG_STOPPED,
        LABEL_CHANNEL_FILTER,
        LABEL_CHANNEL_FILTER_CREATED,
        LABEL_CHANNEL_FILTER_CHANGED,
        LABEL_CHANNEL_FILTER_DELETED,
        LABEL_ESCALATION_CHAIN,
        LABEL_ESCALATION_CHAIN_CREATED,
        LABEL_ESCALATION_CHAIN_DELETED,
        LABEL_ESCALATION_CHAIN_CHANGED,
        LABEL_ESCALATION_POLICY,
        LABEL_ESCALATION_POLICY_CREATED,
        LABEL_ESCALATION_POLICY_DELETED,
        LABEL_ESCALATION_POLICY_CHANGED,
        LABEL_CUSTOM_ACTION,
        LABEL_CUSTOM_ACTION_CREATED,
        LABEL_CUSTOM_ACTION_DELETED,
        LABEL_CUSTOM_ACTION_CHANGED,
        LABEL_SCHEDULE,
        LABEL_SCHEDULE_CREATED,
        LABEL_SCHEDULE_DELETED,
        LABEL_SCHEDULE_CHANGED,
        LABEL_ON_CALL_SHIFT,
        LABEL_ON_CALL_SHIFT_CREATED,
        LABEL_ON_CALL_SHIFT_DELETED,
        LABEL_ON_CALL_SHIFT_CHANGED,
        LABEL_USER,
        LABEL_USER_CREATED,
        LABEL_USER_SETTINGS_CHANGED,
        LABEL_ORGANIZATION_SETTINGS_CHANGED,
        LABEL_TELEGRAM_TO_USER_CONNECTED,
        LABEL_TELEGRAM_FROM_USER_DISCONNECTED,
        LABEL_API_TOKEN,
        LABEL_API_TOKEN_CREATED,
        LABEL_API_TOKEN_REVOKED,
        LABEL_ESCALATION_CHAIN_COPIED,
        LABEL_SCHEDULE_EXPORT_TOKEN,
        LABEL_MESSAGING_BACKEND_CHANNEL_CHANGED,
        LABEL_MESSAGING_BACKEND_CHANNEL_DELETED,
        LABEL_MESSAGING_BACKEND_USER_DISCONNECTED,
    ]

    LABELS_FOR_TYPE = {
        OrganizationLogType.TYPE_SLACK_DEFAULT_CHANNEL_CHANGED: [LABEL_SLACK, LABEL_DEFAULT_CHANNEL],
        OrganizationLogType.TYPE_SLACK_WORKSPACE_CONNECTED: [LABEL_SLACK, LABEL_SLACK_WORKSPACE_CONNECTED],
        OrganizationLogType.TYPE_SLACK_WORKSPACE_DISCONNECTED: [LABEL_SLACK, LABEL_SLACK_WORKSPACE_DISCONNECTED],
        OrganizationLogType.TYPE_TELEGRAM_DEFAULT_CHANNEL_CHANGED: [LABEL_TELEGRAM, LABEL_DEFAULT_CHANNEL],
        OrganizationLogType.TYPE_TELEGRAM_CHANNEL_CONNECTED: [LABEL_TELEGRAM, LABEL_TELEGRAM_CHANNEL_CONNECTED],
        OrganizationLogType.TYPE_TELEGRAM_CHANNEL_DISCONNECTED: [LABEL_TELEGRAM, LABEL_TELEGRAM_CHANNEL_DISCONNECTED],
        OrganizationLogType.TYPE_HEARTBEAT_CREATED: [LABEL_INTEGRATION_HEARTBEAT, LABEL_INTEGRATION_HEARTBEAT_CREATED],
        OrganizationLogType.TYPE_HEARTBEAT_CHANGED: [LABEL_INTEGRATION_HEARTBEAT, LABEL_INTEGRATION_HEARTBEAT_CHANGED],
        OrganizationLogType.TYPE_CHANNEL_FILTER_CREATED: [LABEL_CHANNEL_FILTER, LABEL_CHANNEL_FILTER_CREATED],
        OrganizationLogType.TYPE_CHANNEL_FILTER_DELETED: [LABEL_CHANNEL_FILTER, LABEL_CHANNEL_FILTER_DELETED],
        OrganizationLogType.TYPE_CHANNEL_FILTER_CHANGED: [LABEL_CHANNEL_FILTER, LABEL_CHANNEL_FILTER_CHANGED],
        OrganizationLogType.TYPE_ESCALATION_CHAIN_CREATED: [LABEL_ESCALATION_CHAIN, LABEL_ESCALATION_CHAIN_CREATED],
        OrganizationLogType.TYPE_ESCALATION_CHAIN_DELETED: [LABEL_ESCALATION_CHAIN, LABEL_ESCALATION_CHAIN_DELETED],
        OrganizationLogType.TYPE_ESCALATION_CHAIN_CHANGED: [LABEL_ESCALATION_CHAIN, LABEL_ESCALATION_CHAIN_CHANGED],
        OrganizationLogType.TYPE_ESCALATION_STEP_CREATED: [LABEL_ESCALATION_POLICY, LABEL_ESCALATION_POLICY_CREATED],
        OrganizationLogType.TYPE_ESCALATION_STEP_DELETED: [LABEL_ESCALATION_POLICY, LABEL_ESCALATION_POLICY_DELETED],
        OrganizationLogType.TYPE_ESCALATION_STEP_CHANGED: [LABEL_ESCALATION_POLICY, LABEL_ESCALATION_POLICY_CHANGED],
        OrganizationLogType.TYPE_MAINTENANCE_STARTED_FOR_ORGANIZATION: [
            LABEL_MAINTENANCE,
            LABEL_MAINTENANCE_STARTED,
            LABEL_ORGANIZATION,
        ],
        OrganizationLogType.TYPE_MAINTENANCE_STARTED_FOR_INTEGRATION: [
            LABEL_MAINTENANCE,
            LABEL_MAINTENANCE_STARTED,
            LABEL_INTEGRATION,
        ],
        OrganizationLogType.TYPE_MAINTENANCE_STOPPED_FOR_ORGANIZATION: [
            LABEL_MAINTENANCE,
            LABEL_MAINTENANCE_STOPPED,
            LABEL_ORGANIZATION,
        ],
        OrganizationLogType.TYPE_MAINTENANCE_STOPPED_FOR_INTEGRATION: [
            LABEL_MAINTENANCE,
            LABEL_MAINTENANCE_STOPPED,
            LABEL_INTEGRATION,
        ],
        OrganizationLogType.TYPE_MAINTENANCE_DEBUG_STARTED_FOR_ORGANIZATION: [
            LABEL_DEBUG,
            LABEL_DEBUG_STARTED,
            LABEL_ORGANIZATION,
        ],
        OrganizationLogType.TYPE_MAINTENANCE_DEBUG_STARTED_FOR_INTEGRATION: [
            LABEL_DEBUG,
            LABEL_DEBUG_STARTED,
            LABEL_INTEGRATION,
        ],
        OrganizationLogType.TYPE_MAINTENANCE_DEBUG_STOPPED_FOR_ORGANIZATION: [
            LABEL_DEBUG,
            LABEL_DEBUG_STOPPED,
            LABEL_ORGANIZATION,
        ],
        OrganizationLogType.TYPE_MAINTENANCE_DEBUG_STOPPED_FOR_INTEGRATION: [
            LABEL_DEBUG,
            LABEL_DEBUG_STOPPED,
            LABEL_INTEGRATION,
        ],
        OrganizationLogType.TYPE_CUSTOM_ACTION_CREATED: [LABEL_CUSTOM_ACTION, LABEL_CUSTOM_ACTION_CREATED],
        OrganizationLogType.TYPE_CUSTOM_ACTION_DELETED: [LABEL_CUSTOM_ACTION, LABEL_CUSTOM_ACTION_DELETED],
        OrganizationLogType.TYPE_CUSTOM_ACTION_CHANGED: [LABEL_CUSTOM_ACTION, LABEL_CUSTOM_ACTION_CHANGED],
        OrganizationLogType.TYPE_SCHEDULE_CREATED: [LABEL_SCHEDULE, LABEL_SCHEDULE_CREATED],
        OrganizationLogType.TYPE_SCHEDULE_DELETED: [LABEL_SCHEDULE, LABEL_SCHEDULE_DELETED],
        OrganizationLogType.TYPE_SCHEDULE_CHANGED: [LABEL_SCHEDULE, LABEL_SCHEDULE_CHANGED],
        OrganizationLogType.TYPE_ON_CALL_SHIFT_CREATED: [LABEL_ON_CALL_SHIFT, LABEL_ON_CALL_SHIFT_CREATED],
        OrganizationLogType.TYPE_ON_CALL_SHIFT_DELETED: [LABEL_ON_CALL_SHIFT, LABEL_ON_CALL_SHIFT_DELETED],
        OrganizationLogType.TYPE_ON_CALL_SHIFT_CHANGED: [LABEL_ON_CALL_SHIFT, LABEL_ON_CALL_SHIFT_CHANGED],
        OrganizationLogType.TYPE_NEW_USER_ADDED: [LABEL_USER, LABEL_USER_CREATED],
        OrganizationLogType.TYPE_ORGANIZATION_SETTINGS_CHANGED: [
            LABEL_ORGANIZATION,
            LABEL_ORGANIZATION_SETTINGS_CHANGED,
        ],
        OrganizationLogType.TYPE_USER_SETTINGS_CHANGED: [LABEL_USER, LABEL_USER_SETTINGS_CHANGED],
        OrganizationLogType.TYPE_TELEGRAM_TO_USER_CONNECTED: [LABEL_TELEGRAM, LABEL_TELEGRAM_TO_USER_CONNECTED],
        OrganizationLogType.TYPE_TELEGRAM_FROM_USER_DISCONNECTED: [
            LABEL_TELEGRAM,
            LABEL_TELEGRAM_FROM_USER_DISCONNECTED,
        ],
        OrganizationLogType.TYPE_API_TOKEN_CREATED: [LABEL_API_TOKEN, LABEL_API_TOKEN_CREATED],
        OrganizationLogType.TYPE_API_TOKEN_REVOKED: [LABEL_API_TOKEN, LABEL_API_TOKEN_REVOKED],
        OrganizationLogType.TYPE_ESCALATION_CHAIN_COPIED: [LABEL_ESCALATION_CHAIN, LABEL_ESCALATION_CHAIN_COPIED],
        OrganizationLogType.TYPE_SCHEDULE_EXPORT_TOKEN_CREATED: [
            LABEL_SCHEDULE_EXPORT_TOKEN,
            LABEL_SCHEDULE_EXPORT_TOKEN_CREATED,
        ],
        OrganizationLogType.TYPE_MESSAGING_BACKEND_CHANNEL_CHANGED: [LABEL_MESSAGING_BACKEND_CHANNEL_CHANGED],
        OrganizationLogType.TYPE_MESSAGING_BACKEND_CHANNEL_DELETED: [LABEL_MESSAGING_BACKEND_CHANNEL_DELETED],
        OrganizationLogType.TYPE_MESSAGING_BACKEND_USER_DISCONNECTED: [LABEL_MESSAGING_BACKEND_USER_DISCONNECTED],
    }

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_organization_log,
    )

    organization = models.ForeignKey(
        "user_management.Organization", on_delete=models.CASCADE, related_name="log_records"
    )
    author = models.ForeignKey(
        "user_management.User",
        on_delete=models.SET_NULL,
        related_name="team_log_records",
        default=None,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, default=None)
    _labels = JSONField(default=list)

    @property
    def labels(self):
        return self._labels

    @staticmethod
    def get_log_type_and_maintainable_object_verbal(maintainable_obj, mode, verbal, stopped=False):
        AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
        Organization = apps.get_model("user_management", "Organization")
        object_verbal_map = {
            AlertReceiveChannel: f"integration {emojize(verbal, use_aliases=True)}",
            Organization: "organization",
        }
        if stopped:
            log_type_map = {
                AlertReceiveChannel: {
                    MaintainableObject.DEBUG_MAINTENANCE: OrganizationLogType.TYPE_MAINTENANCE_DEBUG_STOPPED_FOR_INTEGRATION,
                    MaintainableObject.MAINTENANCE: OrganizationLogType.TYPE_MAINTENANCE_STOPPED_FOR_INTEGRATION,
                },
                Organization: {
                    MaintainableObject.DEBUG_MAINTENANCE: OrganizationLogType.TYPE_MAINTENANCE_DEBUG_STOPPED_FOR_ORGANIZATION,
                    MaintainableObject.MAINTENANCE: OrganizationLogType.TYPE_MAINTENANCE_STOPPED_FOR_ORGANIZATION,
                },
            }
        else:
            log_type_map = {
                AlertReceiveChannel: {
                    MaintainableObject.DEBUG_MAINTENANCE: OrganizationLogType.TYPE_MAINTENANCE_DEBUG_STARTED_FOR_INTEGRATION,
                    MaintainableObject.MAINTENANCE: OrganizationLogType.TYPE_MAINTENANCE_STARTED_FOR_INTEGRATION,
                },
                Organization: {
                    MaintainableObject.DEBUG_MAINTENANCE: OrganizationLogType.TYPE_MAINTENANCE_DEBUG_STARTED_FOR_ORGANIZATION,
                    MaintainableObject.MAINTENANCE: OrganizationLogType.TYPE_MAINTENANCE_STARTED_FOR_ORGANIZATION,
                },
            }
        log_type = log_type_map[type(maintainable_obj)][mode]
        object_verbal = object_verbal_map[type(maintainable_obj)]
        return log_type, object_verbal
