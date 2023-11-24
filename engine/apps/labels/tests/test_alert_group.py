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
    alert_receive_channel = make_alert_receive_channel(organization)
    label = make_integration_label_association(organization, alert_receive_channel)
    make_integration_label_association(organization, alert_receive_channel, inheritable=False)

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    assert alert.group.labels.count() == 1
    assert alert.group.labels.first().key_name == label.key.name
    assert alert.group.labels.first().value_name == label.value.name
