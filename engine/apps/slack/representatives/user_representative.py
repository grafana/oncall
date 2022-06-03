from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.user_management.user_representative import UserAbstractRepresentative


class UserSlackRepresentative(UserAbstractRepresentative):
    def __init__(self, log_record):
        self.log_record = log_record

    def is_applicable(self):
        return (
            self.log_record.alert_group.slack_message is not None
            and self.log_record.alert_group.channel.organization.slack_team_identity is not None
        )

    @classmethod
    def on_user_action_triggered(cls, **kwargs):
        log_record = kwargs["log_record"]
        instance = cls(log_record)
        if instance.is_applicable():
            handler_name = instance.get_handler_name()
            if hasattr(instance, handler_name):
                handler = getattr(instance, handler_name)
                handler()
            else:
                cls.on_handler_not_found()

    def on_triggered(self):
        NotificationDeliveryStep = ScenarioStep.get_step("notification_delivery", "NotificationDeliveryStep")
        step = NotificationDeliveryStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_failed(self):
        NotificationDeliveryStep = ScenarioStep.get_step("notification_delivery", "NotificationDeliveryStep")
        step = NotificationDeliveryStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def on_success(self):
        NotificationDeliveryStep = ScenarioStep.get_step("notification_delivery", "NotificationDeliveryStep")
        step = NotificationDeliveryStep(self.log_record.alert_group.channel.organization.slack_team_identity)
        step.process_signal(self.log_record)

    def get_handler_name(self):
        return self.HANDLER_PREFIX + self.get_handlers_map()[self.log_record.type]

    @classmethod
    def on_handler_not_found(cls):
        pass
