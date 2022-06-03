from apps.alerts.incident_appearance.templaters import AlertWebTemplater
from apps.base.messaging import BaseMessagingBackend


class TestOnlyTemplater(AlertWebTemplater):
    def _render_for(self):
        return "testonly"


class TestOnlyBackend(BaseMessagingBackend):
    backend_id = "TESTONLY"
    label = "Test Only Backend"
    short_label = "Test"
    available_for_use = True
    templater = "apps.base.tests.messaging_backend.TestOnlyTemplater"

    def generate_channel_verification_code(self, organization):
        return "42"

    def generate_user_verification_code(self, user):
        return "42"

    def serialize_user(self, user):
        return {"user": user.username}

    def notify_user(self, user, alert_group, notification_policy):
        return
