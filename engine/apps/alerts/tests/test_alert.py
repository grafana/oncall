from unittest.mock import PropertyMock, patch

import pytest
from django.utils import timezone

from apps.alerts.models import Alert, ChannelFilter, EscalationPolicy
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning


@pytest.mark.django_db
@patch("apps.alerts.tasks.distribute_alert.send_alert_create_signal.apply_async", return_value=None)
def test_alert_create_default_channel_filter(
    mocked_send_alert_create_signal,
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    django_capture_on_commit_callbacks,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, is_default=True)

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        alert = Alert.create(
            title="the title",
            message="the message",
            alert_receive_channel=alert_receive_channel,
            raw_request_data={},
            integration_unique_data={},
            image_url=None,
            link_to_upstream_details=None,
        )
    assert alert.group.channel_filter == channel_filter
    assert len(callbacks) == 1
    mocked_send_alert_create_signal.assert_called_once_with((alert.pk,))


@pytest.mark.django_db
def test_alert_create_custom_channel_filter(make_organization, make_alert_receive_channel, make_channel_filter):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_channel_filter(alert_receive_channel, is_default=True)
    other_channel_filter = make_channel_filter(alert_receive_channel)

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
        channel_filter=other_channel_filter,
    )

    assert alert.group.channel_filter == other_channel_filter


@patch("apps.alerts.models.alert.assign_labels")
@patch("apps.alerts.models.alert.gather_labels_from_alert_receive_channel_and_raw_request_data")
@patch("apps.alerts.models.ChannelFilter.select_filter", wraps=ChannelFilter.select_filter)
@pytest.mark.django_db
def test_alert_create_labels_are_assigned(
    spy_channel_filter_select_filter,
    mock_gather_labels_from_alert_receive_channel_and_raw_request_data,
    mock_assign_labels,
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_channel_filter(alert_receive_channel, is_default=True)

    raw_request_data = {"foo": "bar"}

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data=raw_request_data,
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    mock_parsed_labels = mock_gather_labels_from_alert_receive_channel_and_raw_request_data.return_value

    mock_gather_labels_from_alert_receive_channel_and_raw_request_data.assert_called_once_with(
        alert_receive_channel, raw_request_data
    )
    spy_channel_filter_select_filter.assert_called_once_with(
        alert_receive_channel, raw_request_data, mock_parsed_labels
    )
    mock_assign_labels.assert_called_once_with(alert.group, alert_receive_channel, mock_parsed_labels)


@pytest.mark.django_db
def test_alert_create_track_received_at_timestamp(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)

    now = timezone.now()
    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
        received_at=now.isoformat(),
    )

    alert_group = alert.group
    alert_group.refresh_from_db()
    assert alert_group.received_at == now


@patch("apps.alerts.models.AlertGroup.start_escalation_if_needed", return_value=None)
@pytest.mark.django_db
def test_distribute_alert_escalate_alert_group(
    mock_start_escalation,
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert,
    make_escalation_chain,
    make_escalation_policy,
):
    """
    Check start_escalation_if_needed is called for the first alert in the group and not called for the second alert in the group.
    """
    organization = make_organization()
    escalation_chain = make_escalation_chain(organization)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)

    # Check start_escalation_if_needed is called for the first alert in the group
    Alert.create(
        title="the title",
        message="the message",
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
        raw_request_data=alert_receive_channel.config.example_payload,
        alert_receive_channel=alert_receive_channel,
        channel_filter=channel_filter,
    )
    mock_start_escalation.assert_called_once()
    mock_start_escalation.reset_mock()

    # Check start_escalation_if_needed is not called for the second alert in the group
    Alert.create(
        title="the title",
        message="the message",
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
        raw_request_data=alert_receive_channel.config.example_payload,
        alert_receive_channel=alert_receive_channel,
        channel_filter=channel_filter,
    )
    mock_start_escalation.assert_not_called()


@patch("apps.alerts.models.AlertGroup.start_escalation_if_needed", return_value=None)
@pytest.mark.django_db
def test_distribute_alert_escalate_alert_group_when_escalation_paused(
    mock_start_escalation,
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert,
    make_escalation_chain,
    make_escalation_policy,
):
    """
    Check start_escalation_if_needed is called for the first alert in the group and for the second alert in the group
    when escalation is paused.
    """
    organization = make_organization()
    escalation_chain = make_escalation_chain(organization)
    make_escalation_policy(
        escalation_chain=escalation_chain,
        escalation_policy_step=EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS,
    )
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(alert_receive_channel, escalation_chain=escalation_chain)

    # Check start_escalation_if_needed is called for the first alert in the group
    Alert.create(
        title="the title",
        message="the message",
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
        raw_request_data=alert_receive_channel.config.example_payload,
        alert_receive_channel=alert_receive_channel,
        channel_filter=channel_filter,
    )
    mock_start_escalation.assert_called_once()
    mock_start_escalation.reset_mock()

    # Check start_escalation_if_needed is called for the second alert in the group when escalation is paused
    with patch(
        "apps.alerts.escalation_snapshot.escalation_snapshot_mixin.EscalationSnapshotMixin.pause_escalation",
        new_callable=PropertyMock(return_value=True),
    ):
        Alert.create(
            title="the title",
            message="the message",
            integration_unique_data={},
            image_url=None,
            link_to_upstream_details=None,
            raw_request_data=alert_receive_channel.config.example_payload,
            alert_receive_channel=alert_receive_channel,
            channel_filter=channel_filter,
        )
        mock_start_escalation.assert_called_once()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "template,check_if_templated_value_is_truthy,expected",
    [
        ('{{ "foo" in labels.keys() }}', True, True),
        (' {{ "foo" in labels.keys() }} ', False, " True "),
    ],
)
def test_apply_jinja_template_to_alert_payload_and_labels(
    make_organization, make_alert_receive_channel, template, check_if_templated_value_is_truthy, expected
):
    template_name = "test_template_name"
    raw_request_data = {"value": 5}
    labels = {"foo": "bar"}

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)

    assert (
        Alert._apply_jinja_template_to_alert_payload_and_labels(
            template,
            template_name,
            alert_receive_channel,
            raw_request_data,
            labels,
            check_if_templated_value_is_truthy=check_if_templated_value_is_truthy,
        )
        == expected
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ExceptionClass,use_error_msg_as_fallback,check_if_templated_value_is_truthy,expected",
    [
        (JinjaTemplateError, True, False, "Template Error: asdflkjqwerqwer"),
        (JinjaTemplateWarning, True, False, "Template Warning: asdflkjqwerqwer"),
        (JinjaTemplateError, False, True, False),
        (JinjaTemplateWarning, False, True, False),
        (JinjaTemplateError, False, False, None),
        (JinjaTemplateWarning, False, False, None),
    ],
)
@patch("apps.alerts.models.alert.apply_jinja_template_to_alert_payload_and_labels")
def test_apply_jinja_template_to_alert_payload_and_labels_jinja_exceptions(
    mock_apply_jinja_template_to_alert_payload_and_labels,
    make_organization,
    make_alert_receive_channel,
    ExceptionClass,
    use_error_msg_as_fallback,
    check_if_templated_value_is_truthy,
    expected,
):
    mock_apply_jinja_template_to_alert_payload_and_labels.side_effect = ExceptionClass("asdflkjqwerqwer")

    template = "hi"
    template_name = "test_template_name"
    raw_request_data = {"value": 5}
    labels = {"foo": "bar"}

    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)

    result = Alert._apply_jinja_template_to_alert_payload_and_labels(
        template,
        template_name,
        alert_receive_channel,
        raw_request_data,
        labels,
        use_error_msg_as_fallback=use_error_msg_as_fallback,
        check_if_templated_value_is_truthy=check_if_templated_value_is_truthy,
    )
    assert result == expected

    mock_apply_jinja_template_to_alert_payload_and_labels.assert_called_once_with(template, raw_request_data, labels)
