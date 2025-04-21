import logging

from rest_framework import status

from apps.alerts.models import AlertGroup
from apps.alerts.representative import AlertGroupAbstractRepresentative
from apps.mattermost.alert_rendering import MattermostMessageRenderer
from apps.mattermost.client import MattermostClient
from apps.mattermost.exceptions import MattermostAPIException, MattermostAPITokenInvalid
from apps.mattermost.tasks import on_alert_group_action_triggered_async, on_create_alert_async

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AlertGroupMattermostRepresentative(AlertGroupAbstractRepresentative):
    def __init__(self, log_record) -> None:
        self.log_record = log_record

    def is_applicable(self):
        from apps.mattermost.models import MattermostChannel

        organization = self.log_record.alert_group.channel.organization
        handler_exists = self.log_record.type in self.get_handler_map().keys()

        mattermost_channels = MattermostChannel.objects.filter(organization=organization)
        return handler_exists and mattermost_channels.exists()

    @staticmethod
    def get_handler_map():
        from apps.alerts.models import AlertGroupLogRecord

        return {
            AlertGroupLogRecord.TYPE_ACK: "alert_group_action",
            AlertGroupLogRecord.TYPE_UN_ACK: "alert_group_action",
            AlertGroupLogRecord.TYPE_AUTO_UN_ACK: "alert_group_action",
            AlertGroupLogRecord.TYPE_RESOLVED: "alert_group_action",
            AlertGroupLogRecord.TYPE_UN_RESOLVED: "alert_group_action",
            AlertGroupLogRecord.TYPE_ACK_REMINDER_TRIGGERED: "alert_group_action",
            AlertGroupLogRecord.TYPE_SILENCE: "alert_group_action",
            AlertGroupLogRecord.TYPE_UN_SILENCE: "alert_group_action",
            AlertGroupLogRecord.TYPE_ATTACHED: "alert_group_action",
            AlertGroupLogRecord.TYPE_UNATTACHED: "alert_group_action",
        }

    def on_alert_group_action(self, alert_group: AlertGroup):
        logger.info(f"Update mattermost message for alert_group {alert_group.pk}")
        payload = MattermostMessageRenderer(alert_group).render_alert_group_message()
        mattermost_message = alert_group.mattermost_messages.order_by("created_at").first()
        try:
            client = MattermostClient()
            client.update_post(post_id=mattermost_message.post_id, data=payload)
        except MattermostAPITokenInvalid:
            logger.error(f"Mattermost API token is invalid could not create post for alert {alert_group.pk}")
        except MattermostAPIException as ex:
            logger.error(f"Mattermost API error {ex}")
            if ex.status not in [status.HTTP_401_UNAUTHORIZED]:
                raise ex

    @staticmethod
    def on_create_alert(**kwargs):
        alert_pk = kwargs["alert"]
        on_create_alert_async.apply_async((alert_pk,))

    @staticmethod
    def on_alert_group_action_triggered(**kwargs):
        from apps.alerts.models import AlertGroupLogRecord

        log_record = kwargs["log_record"]
        if isinstance(log_record, AlertGroupLogRecord):
            log_record_id = log_record.pk
        else:
            log_record_id = log_record
        on_alert_group_action_triggered_async.apply_async((log_record_id,))

    def get_handler(self):
        handler_name = self.get_handler_name()
        logger.info(f"Using '{handler_name}' handler to process alert action in mattermost")
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
        else:
            handler = None

        return handler

    def get_handler_name(self):
        return self.HANDLER_PREFIX + self.get_handler_map()[self.log_record.type]
