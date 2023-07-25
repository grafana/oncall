from apps.alerts.incident_appearance.templaters import AlertWebTemplater
from apps.base.messaging import BaseMessagingBackend


class TestOnlyTemplater(AlertWebTemplater):
    def _render_for(self):
        return "testonly"


class TestOnlyBackend(BaseMessagingBackend):
    """
    set a __test__ = False attribute in classes that pytest should ignore otherwise we end up getting the following:
    PytestCollectionWarning: cannot collect test class 'TestOnlyBackend' because it has a __init__ constructor
    """

    __test__ = False

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
