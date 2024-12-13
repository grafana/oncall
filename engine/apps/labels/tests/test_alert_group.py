from unittest import mock

import pytest

from apps.alerts.models import Alert
from apps.labels.models import MAX_KEY_NAME_LENGTH, MAX_VALUE_NAME_LENGTH, LabelKeyCache, LabelValueCache

TOO_LONG_KEY_NAME = "k" * (MAX_KEY_NAME_LENGTH + 1)
TOO_LONG_VALUE_NAME = "v" * (MAX_VALUE_NAME_LENGTH + 1)


@mock.patch("apps.labels.alert_group_labels.is_labels_feature_enabled", return_value=False)
@pytest.mark.django_db
def test_assign_labels_feature_flag_disabled(
    _, make_organization, make_alert_receive_channel, make_static_label_config
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_static_label_config(organization, alert_receive_channel)

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
def test_multi_label_extraction_template(
    make_organization,
    make_alert_receive_channel,
    make_label_key_and_value,
    make_label_key,
    make_static_label_config,
):
    organization = make_organization()

    # create alert receive channel with all 3 types of labels
    alert_receive_channel = make_alert_receive_channel(
        organization,
        alert_group_labels_template="{{ payload.advanced_template | tojson }}",
    )

    # create alert group
    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={
            "advanced_template": {
                "cluster_id": 123,
                "severity": "critical",
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
        ("cluster_id", "123"),
        ("severity", "critical"),
    ]


@pytest.mark.django_db
def test_assign_dynamic_labels(
    make_organization,
    make_alert_receive_channel,
    make_label_key_and_value,
    make_label_key,
    make_label_value,
):
    organization = make_organization()

    # create label repo labels
    label_key_severity = make_label_key(organization=organization, key_name="severity")
    label_key_service = make_label_key(organization=organization, key_name="service")
    # add values for severity key
    _ = make_label_value(label_key_severity, value_name="critical")

    # set-up some keys to test invalid templates
    label_key_cluster = make_label_key(organization=organization, key_name="cluster")
    label_key_region = make_label_key(organization=organization, key_name="region")
    label_key_team = make_label_key(organization=organization, key_name="team")

    # create alert receive channel with all 3 types of labels
    alert_receive_channel = make_alert_receive_channel(
        organization,
        alert_group_labels_custom=[
            # valid templated label, parsed value present in label repo. Expected to be attached to group,
            [label_key_severity.id, None, "{{ payload.severity }}"],
            # valid templated label, parsed value NOT present in label repo  Expected to be attached anyway.
            [label_key_service.id, None, "{{ payload.service }}"],
            # templated label too long.  Expected to be ignored
            [label_key_cluster.id, None, TOO_LONG_VALUE_NAME],
            # templated label with jinja template pointing to nonexistent attribute in alert payload,  Expected to be ignored
            [label_key_region.id, None, "{{ payload.nonexistent }}"],
            # templated label explicitly set to None. Expected to be ignored
            [label_key_team.id, None, "{{ payload.nonexistent or None }}"],
            # templated label with nonexistent key ID. Expected to be ignored
            ["nonexistent", None, "{{ payload.severity }}"],
        ],
    )
    # create alert group
    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={
            "severity": "critical",
            "service": "oncall",
            "extra": "hi",
        },
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    assert [(label.key_name, label.value_name) for label in alert.group.labels.all()] == [
        ("service", "oncall"),
        ("severity", "critical"),
    ]


@pytest.mark.django_db
def test_assign_static_labels(
    make_organization,
    make_alert_receive_channel,
    make_static_label_config,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization, alert_group_labels_custom=None)
    # Configure a static label - expected to be attached to group.
    make_static_label_config(organization, alert_receive_channel, key_name="severity", value_name="critical")

    # Configure a static label & delete key and value caches. Expected to be ignored.
    make_static_label_config(organization, alert_receive_channel, key_name="service", value_name="oncall")
    key = LabelKeyCache.objects.get(name="service")
    LabelValueCache.objects.filter(name="oncall", key=key).delete()
    key.delete()

    alert = Alert.create(
        title="the title",
        message="the message",
        alert_receive_channel=alert_receive_channel,
        raw_request_data={},
        integration_unique_data={},
        image_url=None,
        link_to_upstream_details=None,
    )

    assert [(label.key_name, label.value_name) for label in alert.group.labels.all()] == [("severity", "critical")]


@pytest.mark.django_db
def test_assign_labels_too_many(
    make_organization, make_alert_receive_channel, make_static_label_config, make_label_key_and_value
):
    organization = make_organization()

    label_key, label_value = make_label_key_and_value(organization, key_name="a", value_name="test")
    alert_receive_channel = make_alert_receive_channel(
        organization,
        alert_group_labels_template='{{ {"b": payload.b} | tojson }}',
    )
    make_static_label_config(organization, alert_receive_channel, key_name="a", value_name="test")
    make_static_label_config(organization, alert_receive_channel, key_name="c", value_name="test")

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
