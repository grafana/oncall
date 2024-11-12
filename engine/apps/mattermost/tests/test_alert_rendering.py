import pytest
from django.utils import timezone

from apps.mattermost.alert_rendering import MattermostMessageRenderer


@pytest.mark.django_db
@pytest.mark.parametrize(
    "expected_button_ids,expected_button_names,color_code,alert_type",
    [
        (["acknowledge", "resolve"], ["Acknowledge", "Resolve"], "#a30200", "unack"),
        (["unacknowledge", "resolve"], ["Unacknowledge", "Resolve"], "#daa038", "ack"),
        (["unresolve"], ["Unresolve"], "#2eb886", "resolved"),
    ],
)
def test_alert_group_message_renderer(
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    expected_button_ids,
    expected_button_names,
    color_code,
    alert_type,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)

    if alert_type == "unack":
        alert_group = make_alert_group(alert_receive_channel)
        make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    elif alert_type == "ack":
        alert_group = make_alert_group(
            alert_receive_channel, acknowledged_at=timezone.now() + timezone.timedelta(hours=1), acknowledged=True
        )
        make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    elif alert_type == "resolved":
        alert_group = make_alert_group(
            alert_receive_channel, resolved_at=timezone.now() + timezone.timedelta(hours=1), resolved=True
        )
        make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    message = MattermostMessageRenderer(alert_group=alert_group).render_alert_group_message()
    actions = message["props"]["attachments"][0]["actions"]
    color = message["props"]["attachments"][0]["color"]
    assert color == color_code
    ids = [a["id"] for a in actions]
    for id in ids:
        assert id in expected_button_ids
    names = [a["name"] for a in actions]
    for name in names:
        assert name in expected_button_names
