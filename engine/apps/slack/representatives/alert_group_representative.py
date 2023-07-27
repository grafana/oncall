import logging

from celery.utils.log import get_task_logger
from django.conf import settings

from apps.alerts.constants import ActionSource
from apps.alerts.representative import AlertGroupAbstractRepresentative
from apps.slack.scenarios.scenario_step import ScenarioStep
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_create_alert_slack_representative_async(alert_pk):
    """
    It's asynced in order to prevent Slack downtime causing issues with SMS and other destinations.
    """
    from apps.alerts.models import Alert

    alert = (
        Alert.objects.filter(pk=alert_pk)
        .select_related(
            "group",
            "group__channel",
            "group__channel__organization",
            "group__channel__organization__slack_team_identity",
        )
        .get()
    )
    logger.debug(f"Start on_create_alert_slack_representative for alert {alert_pk} from alert_group {alert.group_id}")

    organization = alert.group.channel.organization
    if organization.slack_team_identity:
        logger.debug(
            f"Process on_create_alert_slack_representative for alert {alert_pk} from alert_group {alert.group_id}"
        )
        AlertShootingStep = ScenarioStep.get_step("distribute_alerts", "AlertShootingStep")
        step = AlertShootingStep(organization.slack_team_identity, organization)
        step.process_signal(alert)
    else:
        logger.debug(
            f"Drop on_create_alert_slack_representative for alert {alert_pk} from alert_group {alert.group_id}"
        )
    logger.debug(f"Finish on_create_alert_slack_representative for alert {alert_pk} from alert_group {alert.group_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_alert_group_action_triggered_async(log_record_id):
    from apps.alerts.models import AlertGroupLogRecord

    logger.debug(f"SLACK representative: get log record {log_record_id}")

    log_record = AlertGroupLogRecord.objects.get(pk=log_record_id)
    alert_group_id = log_record.alert_group_id
    logger.debug(f"Start on_alert_group_action_triggered for alert_group {alert_group_id}, log record {log_record_id}")
    instance = AlertGroupSlackRepresentative(log_record)
    if instance.is_applicable():
        logger.debug(f"SLACK representative is applicable for alert_group {alert_group_id}, log record {log_record_id}")
        handler = instance.get_handler()
        logger.debug(
            f"Found handler {handler.__name__} in SLACK representative for alert_group {alert_group_id}, "
            f"log record {log_record_id}"
        )
        handler()
        logger.debug(
            f"Finish handler {handler.__name__} in SLACK representative for alert_group {alert_group_id}, "
            f"log record {log_record_id}"
        )
    else:
        logger.debug(
            f"SLACK representative is NOT applicable for alert_group {alert_group_id}, log record {log_record_id}"
        )
    logger.debug(f"Finish on_alert_group_action_triggered for alert_group {alert_group_id}, log record {log_record_id}")


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def on_alert_group_update_log_report_async(alert_group_id):
    from apps.alerts.models import AlertGroup

    alert_group = AlertGroup.objects.get(pk=alert_group_id)
    logger.debug(f"Start on_alert_group_update_log_report for alert_group {alert_group_id}")
    organization = alert_group.channel.organization
    if alert_group.slack_message and organization.slack_team_identity:
        logger.debug(f"Process on_alert_group_update_log_report for alert_group {alert_group_id}")
        UpdateLogReportMessageStep = ScenarioStep.get_step("distribute_alerts", "UpdateLogReportMessageStep")
        step = UpdateLogReportMessageStep(organization.slack_team_identity, organization)
        step.process_signal(alert_group)
    else:
        logger.debug(f"Drop on_alert_group_update_log_report for alert_group {alert_group_id}")
    logger.debug(f"Finish on_alert_group_update_log_report for alert_group {alert_group_id}")


class AlertGroupSlackRepresentative(AlertGroupAbstractRepresentative):
    def __init__(self, log_record):
        self.log_record = log_record

    def is_applicable(self):
        slack_message = self.log_record.alert_group.get_slack_message()
        slack_team_identity = self.log_record.alert_group.channel.organization.slack_team_identity
        return (
            slack_message is not None
            and slack_team_identity is not None
            and slack_message.slack_team_identity == slack_team_identity
        )

    @classmethod
    def on_create_alert(cls, **kwargs):
        from apps.alerts.models import Alert

        alert = kwargs["alert"]
        if isinstance(alert, Alert):
            alert_id = alert.pk
        else:
            alert_id = alert
            alert = Alert.objects.get(pk=alert_id)

        logger.debug(
            f"Received alert_create_signal in SLACK representative for alert {alert_id} "
            f"from alert_group {alert.group_id}"
        )

        if alert.group.notify_in_slack_enabled is False:
            logger.debug(
                f"Skipping alert with id {alert_id} from alert_group {alert.group_id} since notify_in_slack is disabled"
            )
            return
        on_create_alert_slack_representative_async.apply_async((alert_id,))

        logger.debug(
            f"Async process alert_create_signal in SLACK representative for alert {alert_id} "
            f"from alert_group {alert.group_id}"
        )

    @classmethod
    def on_alert_group_action_triggered(cls, **kwargs):
        logger.debug("Received alert_group_action_triggered signal in SLACK representative")
        from apps.alerts.models import AlertGroupLogRecord

        log_record = kwargs["log_record"]
        action_source = kwargs.get("action_source")
        force_sync = kwargs.get("force_sync", False)
        if isinstance(log_record, AlertGroupLogRecord):
            log_record_id = log_record.pk
        else:
            log_record_id = log_record

        if action_source == ActionSource.SLACK or force_sync:
            on_alert_group_action_triggered_async(log_record_id)
        else:
            on_alert_group_action_triggered_async.apply_async((log_record_id,))

    @classmethod
    def on_alert_group_update_log_report(cls, **kwargs):
        from apps.alerts.models import AlertGroup

        alert_group = kwargs["alert_group"]

        if isinstance(alert_group, AlertGroup):
            alert_group_id = alert_group.pk
        else:
            alert_group_id = alert_group
            alert_group = AlertGroup.objects.get(pk=alert_group_id)

        logger.debug(
            f"Received alert_group_update_log_report signal in SLACK representative for alert_group {alert_group_id}"
        )

        if alert_group.notify_in_slack_enabled is False:
            logger.debug(f"Skipping alert_group {alert_group_id} since notify_in_slack is disabled")
            return

        on_alert_group_update_log_report_async.apply_async((alert_group_id,))

    @classmethod
    def on_alert_group_update_resolution_note(cls, **kwargs):
        alert_group = kwargs["alert_group"]
        resolution_note = kwargs.get("resolution_note")
        organization = alert_group.channel.organization
        logger.debug(
            f"Received alert_group_update_resolution_note signal in SLACK representative for alert_group {alert_group.pk}"
        )
        if alert_group.slack_message and organization.slack_team_identity:
            UpdateResolutionNoteStep = ScenarioStep.get_step("resolution_note", "UpdateResolutionNoteStep")
            step = UpdateResolutionNoteStep(organization.slack_team_identity, organization)
            step.process_signal(alert_group, resolution_note)

    def on_acknowledge(self):
        AcknowledgeGroupStep = ScenarioStep.get_step("distribute_alerts", "AcknowledgeGroupStep")
        step = AcknowledgeGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_un_acknowledge(self):
        UnAcknowledgeGroupStep = ScenarioStep.get_step("distribute_alerts", "UnAcknowledgeGroupStep")
        step = UnAcknowledgeGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_resolve(self):
        ResolveGroupStep = ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep")
        step = ResolveGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_un_resolve(self):
        UnResolveGroupStep = ScenarioStep.get_step("distribute_alerts", "UnResolveGroupStep")
        step = UnResolveGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_attach(self):
        AttachGroupStep = ScenarioStep.get_step("distribute_alerts", "AttachGroupStep")
        step = AttachGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_fail_attach(self):
        AttachGroupStep = ScenarioStep.get_step("distribute_alerts", "AttachGroupStep")
        step = AttachGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_un_attach(self):
        UnAttachGroupStep = ScenarioStep.get_step("distribute_alerts", "UnAttachGroupStep")
        step = UnAttachGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_silence(self):
        SilenceGroupStep = ScenarioStep.get_step("distribute_alerts", "SilenceGroupStep")
        step = SilenceGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_un_silence(self):
        UnSilenceGroupStep = ScenarioStep.get_step("distribute_alerts", "UnSilenceGroupStep")
        step = UnSilenceGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_invite(self):
        InviteOtherPersonToIncident = ScenarioStep.get_step("distribute_alerts", "InviteOtherPersonToIncident")
        step = InviteOtherPersonToIncident(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_re_invite(self):
        self.on_invite()

    def on_un_invite(self):
        StopInvitationProcess = ScenarioStep.get_step("distribute_alerts", "StopInvitationProcess")
        step = StopInvitationProcess(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_auto_un_acknowledge(self):
        self.on_un_acknowledge()

    def on_ack_reminder_triggered(self):
        AcknowledgeConfirmationStep = ScenarioStep.get_step("distribute_alerts", "AcknowledgeConfirmationStep")
        step = AcknowledgeConfirmationStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_custom_button_triggered(self):
        CustomButtonProcessStep = ScenarioStep.get_step("distribute_alerts", "CustomButtonProcessStep")
        step = CustomButtonProcessStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_wiped(self):
        WipeGroupStep = ScenarioStep.get_step("distribute_alerts", "WipeGroupStep")
        step = WipeGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_deleted(self):
        DeleteGroupStep = ScenarioStep.get_step("distribute_alerts", "DeleteGroupStep")
        step = DeleteGroupStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def get_handler(self):
        handler_name = self.get_handler_name()
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
