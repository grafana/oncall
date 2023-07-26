import logging

from apps.alerts.models import AlertGroup
from apps.alerts.representative import AlertGroupAbstractRepresentative
from apps.telegram.models import TelegramMessage
from apps.telegram.tasks import edit_message, on_create_alert_telegram_representative_async

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AlertGroupTelegramRepresentative(AlertGroupAbstractRepresentative):
    def __init__(self, log_record):
        self.log_record = log_record

    def is_applicable(self):
        from apps.telegram.models import TelegramToOrganizationConnector, TelegramToUserConnector

        organization = self.log_record.alert_group.channel.organization

        handler_exists = self.log_record.type in self.get_handlers_map().keys()

        telegram_org_connector = TelegramToOrganizationConnector.objects.filter(organization=organization)
        telegram_channel_configured = telegram_org_connector.exists() and telegram_org_connector[0].is_configured

        is_user_in_org_using_telegram = TelegramToUserConnector.objects.filter(user__organization=organization).exists()

        return handler_exists and (telegram_channel_configured or is_user_in_org_using_telegram)

    @staticmethod
    def get_handlers_map():
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

    # Process all alert group actions (ack, resolve, etc.)
    def on_alert_group_action(self):
        messages_to_edit = self.log_record.alert_group.telegram_messages.filter(
            message_type__in=(
                TelegramMessage.ALERT_GROUP_MESSAGE,
                TelegramMessage.ACTIONS_MESSAGE,
                TelegramMessage.PERSONAL_MESSAGE,
            )
        )
        for message in messages_to_edit:
            edit_message.delay(message_pk=message.pk)

    @classmethod
    def on_alert_group_update_log_report(cls, **kwargs):
        logger.info("AlertGroupTelegramRepresentative UPDATE LOG REPORT SIGNAL")
        alert_group = kwargs["alert_group"]
        if not isinstance(alert_group, AlertGroup):
            alert_group = AlertGroup.objects.get(pk=alert_group)

        messages_to_edit = alert_group.telegram_messages.filter(
            message_type__in=(
                TelegramMessage.LOG_MESSAGE,
                TelegramMessage.PERSONAL_MESSAGE,
            )
        )

        for message in messages_to_edit:
            edit_message.delay(message_pk=message.pk)

    @classmethod
    def on_alert_group_action_triggered(cls, **kwargs):
        from apps.alerts.models import AlertGroupLogRecord

        log_record = kwargs["log_record"]
        logger.info(f"AlertGroupTelegramRepresentative ACTION SIGNAL, log record {log_record}")

        if not isinstance(log_record, AlertGroupLogRecord):
            log_record = AlertGroupLogRecord.objects.get(pk=log_record)

        instance = cls(log_record)
        if instance.is_applicable():
            handler = instance.get_handler()
            handler()

    @staticmethod
    def on_create_alert(**kwargs):
        alert_pk = kwargs["alert"]
        on_create_alert_telegram_representative_async.apply_async((alert_pk,))

    def get_handler(self):
        handler_name = self.get_handler_name()
        logger.info(f"Using '{handler_name}' handler to process action signal")
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
        else:
            handler = self.on_handler_not_found

        return handler

    def get_handler_name(self):
        return self.HANDLER_PREFIX + self.get_handlers_map()[self.log_record.type]

    @classmethod
    def on_handler_not_found(cls):
        pass
