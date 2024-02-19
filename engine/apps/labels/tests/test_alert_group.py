from unittest import mock

import pytest

from apps.alerts.models import Alert
from apps.labels.models import MAX_KEY_NAME_LENGTH, MAX_VALUE_NAME_LENGTH

TOO_LONG_KEY_NAME = "k" * (MAX_KEY_NAME_LENGTH + 1)
TOO_LONG_VALUE_NAME = "v" * (MAX_VALUE_NAME_LENGTH + 1)


@mock.patch("apps.labels.alert_group_labels.is_labels_feature_enabled", return_value=False)
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
    label_key_3 = make_label_key(organization=organization)
    label_key_4 = make_label_key(organization=organization)

    # create alert receive channel with all 3 types of labels
    alert_receive_channel = make_alert_receive_channel(
        organization,
        alert_group_labels_custom=[
            [label_key.id, label_value.id, None],  # plain label
            ["nonexistent", label_value.id, None],  # plain label with nonexistent key ID
            [label_key_2.id, "nonexistent", None],  # plain label with nonexistent value ID
            [label_key_1.id, None, "{{ payload.c }}"],  # templated label
            [label_key_3.id, None, TOO_LONG_VALUE_NAME],  # templated label too long
            [label_key_4.id, None, "{{ payload.nonexistent }}"],  # templated label with nonexistent key
        ],
        alert_group_labels_template="{{ payload.advanced_template | tojson }}",
    )
    make_integration_label_association(organization, alert_receive_channel, key_name="e", value_name="f")

    # create alert group
    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={
            "c": "d",
            "advanced_template": {
                "g": 123,
                "too_long": TOO_LONG_VALUE_NAME,
                TOO_LONG_KEY_NAME: "too_long",
                "invalid_type": {"test": "test"},
            },
            "extra": "hi",
        },
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    # check alert group labels are assigned correctly, in the lexicographical order
    assert [(label.key_name, label.value_name) for label in alert.group.labels.all()] == [
        ("a", "b"),
        ("c", "d"),
        ("e", "f"),
        ("g", "123"),
    ]


@pytest.mark.django_db
def test_assign_labels_custom_labels_none(
    make_organization,
    make_alert_receive_channel,
    make_integration_label_association,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, alert_group_labels_custom=None)
    make_integration_label_association(organization, alert_receive_channel, key_name="a", value_name="b")

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    assert [(label.key_name, label.value_name) for label in alert.group.labels.all()] == [("a", "b")]


@pytest.mark.django_db
def test_assign_labels_too_many(
    make_organization, make_alert_receive_channel, make_integration_label_association, make_label_key_and_value
):
    organization = make_organization()

    label_key, label_value = make_label_key_and_value(organization, key_name="a", value_name="test")
    alert_receive_channel = make_alert_receive_channel(
        organization,
        alert_group_labels_custom=[[label_key.id, label_value.id, None]],
        alert_group_labels_template='{{ {"b": payload.b} | tojson }}',
    )
    make_integration_label_association(organization, alert_receive_channel, key_name="c", value_name="test")

    with mock.patch("apps.labels.alert_group_labels.MAX_LABELS_PER_ALERT_GROUP", 2):
        alert = Alert.create(
            title="the title",
            message="the message",
            alert_receive_channel=alert_receive_channel,
            raw_request_data={"b": "test"},
            integration_unique_data={},
            image_url=None,
            link_to_upstream_details=None,
        )

    # check only 2 labels are assigned and 3rd label is dropped
    assert [(label.key_name, label.value_name) for label in alert.group.labels.all()] == [
        ("a", "test"),
        ("b", "test"),
    ]
