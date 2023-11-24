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
def test_assign_labels(
    make_organization,
    make_alert_receive_channel,
    make_label_key_and_value,
    make_label_key,
    make_integration_label_association,
):
    organization = make_organization()

    # create label repo labels
    label_key, label_value = make_label_key_and_value(organization, key_name="a", value_name="b")
    label_key_1 = make_label_key(organization=organization, key_name="c")
    label_key_2 = make_label_key(organization=organization)

    # create alert receive channel with all 3 types of labels
    alert_receive_channel = make_alert_receive_channel(
        organization,
        alert_group_labels_custom=[
            [label_key.id, label_value.id, None],  # plain label
            ["nonexistent", label_value.id, None],  # plain label with nonexistent key ID
            [label_key_2.id, "nonexistent", None],  # plain label with nonexistent value ID
            [label_key_1.id, None, "{{ payload.c }}"],  # template label
            ["nonexistent", None, "{{ payload.extra }}"],  # template label with nonexistent key ID
        ],
        alert_group_labels_template="{{ payload.advanced_template | tojson }}",
    )
    make_integration_label_association(organization, alert_receive_channel, key_name="e", value_name="f")

    # create alert group
    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={"c": "d", "advanced_template": {"g": "h"}, "extra": "hi"},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    # check alert group labels are assigned correctly, in the lexicographical order
    assert [(label.key_name, label.value_name) for label in alert.group.labels.all()] == [
        ("a", "b"),
        ("c", "d"),
        ("e", "f"),
        ("g", "h"),
    ]
