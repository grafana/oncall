from unittest import mock

import pytest

from apps.alerts.models import Alert


@mock.patch("apps.labels.utils.is_labels_feature_enabled", return_value=False)
@pytest.mark.django_db
def test_assign_labels_feature_flag_disabled(
    _, make_organization, make_alert_receive_channel, make_integration_label_association
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_integration_label_association(organization, alert_receive_channel)

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    assert not alert.group.labels.exists()


@pytest.mark.django_db
def test_assign_labels(make_organization, make_alert_receive_channel, make_integration_label_association):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(
        organization,
        alert_group_labels_custom=[
            {"key": "a", "value": "b", "template": False},
            {"key": "c", "value": "{{ payload.c }}", "template": True},
        ],
        alert_group_labels_template="{{ payload.labels | tojson }}",
    )

    label = make_integration_label_association(organization, alert_receive_channel)
    label.key.name, label.value.name = ("e", "f")
    label.key.save(update_fields=["name"])
    label.value.save(update_fields=["name"])
    make_integration_label_association(organization, alert_receive_channel, inheritable=False)

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={"c": "d", "labels": {"g": "h"}},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    assert [(label.key_name, label.value_name) for label in alert.group.labels.all()] == [
        ("a", "b"),
        ("c", "d"),
        ("e", "f"),
        ("g", "h"),
    ]
