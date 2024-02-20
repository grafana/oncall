import pytest

from apps.alerts.models import AlertReceiveChannel
from apps.labels.models import (
    AlertReceiveChannelAssociatedLabel,
    AssociatedLabel,
    LabelValueCache,
    WebhookAssociatedLabel,
)
from apps.labels.utils import get_associating_label_model, is_labels_feature_enabled
from apps.webhooks.models import Webhook


@pytest.mark.django_db
def test_labels_feature_flag(mock_is_labels_feature_enabled_for_org, make_organization, settings):
    organization = make_organization()
    # returns True if feature flag is enabled
    assert settings.FEATURE_LABELS_ENABLED_FOR_ALL
    assert organization.id not in settings.FEATURE_LABELS_ENABLED_PER_ORG
    assert is_labels_feature_enabled(organization)

    mock_is_labels_feature_enabled_for_org(organization.id)
    # returns True if feature flag is disabled and organization is in the feature list
    assert not settings.FEATURE_LABELS_ENABLED_FOR_ALL
    assert organization.id in settings.FEATURE_LABELS_ENABLED_PER_ORG
    assert is_labels_feature_enabled(organization)

    mock_is_labels_feature_enabled_for_org(12345)
    # returns False if feature flag is disabled and organization is not in the feature list
    assert organization.org_id not in settings.FEATURE_LABELS_ENABLED_PER_ORG

    assert not is_labels_feature_enabled(organization)


@pytest.mark.django_db
def test_labels_feature_flag_when_plugin_is_disabled(
    mock_is_labels_feature_enabled_for_org, make_organization, settings
):
    organization = make_organization()
    organization.is_grafana_labels_enabled = False
    # returns False if feature flag is enabled, but plugin is disabled
    assert settings.FEATURE_LABELS_ENABLED_FOR_ALL
    assert organization.id not in settings.FEATURE_LABELS_ENABLED_PER_ORG
    assert is_labels_feature_enabled(organization) is False

    mock_is_labels_feature_enabled_for_org(organization.id)
    # returns False if feature flag is disabled, organization is in the feature list, , but plugin is disabled
    assert not settings.FEATURE_LABELS_ENABLED_FOR_ALL
    assert organization.id in settings.FEATURE_LABELS_ENABLED_PER_ORG
    assert is_labels_feature_enabled(organization) is False

    assert not is_labels_feature_enabled(organization)


@pytest.mark.django_db
def test_label_associate_new_label(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    label_key_id = "testkeyid"
    label_value_id = "testvalueid"
    labels_data = [
        {
            "key": {"id": label_key_id, "name": "testkey", "prescribed": False},
            "value": {"id": label_value_id, "name": "testvalue", "prescribed": False},
        }
    ]

    assert not alert_receive_channel.labels.exists()
    assert not LabelValueCache.objects.filter(key_id=label_key_id, id=label_value_id).exists()

    AssociatedLabel.update_association(labels_data, alert_receive_channel, organization)
    assert len(alert_receive_channel.labels.all()) == 1
    assert alert_receive_channel.labels.get(key_id=label_key_id, value_id=label_value_id)


@pytest.mark.django_db
def test_label_associate_existing_label(make_label_key_and_value, make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    label_key, label_value = make_label_key_and_value(organization)
    labels_data = [
        {
            "key": {"id": label_key.id, "name": label_key.name, "prescribed": False},
            "value": {"id": label_value.id, "name": label_value.name, "prescribed": False},
        }
    ]
    assert not alert_receive_channel.labels.exists()
    AssociatedLabel.update_association(labels_data, alert_receive_channel, organization)
    assert len(alert_receive_channel.labels.all()) == 1
    assert alert_receive_channel.labels.filter(key=label_key, value=label_value).exists()


@pytest.mark.django_db
def test_label_update_association_by_removing_label(
    make_integration_label_association, make_organization, make_alert_receive_channel
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    label_association_1 = make_integration_label_association(organization, alert_receive_channel)
    label_association_2 = make_integration_label_association(organization, alert_receive_channel)
    labels_data = [
        {
            "key": {"id": label_association_1.key_id, "name": label_association_1.key.name, "prescribed": False},
            "value": {"id": label_association_1.value_id, "name": label_association_1.value.name, "prescribed": False},
        }
    ]

    assert len(alert_receive_channel.labels.all()) == 2
    assert alert_receive_channel.labels.filter(
        key=label_association_1.key_id, value=label_association_1.value_id
    ).exists()
    assert alert_receive_channel.labels.filter(
        key=label_association_2.key_id, value=label_association_2.value_id
    ).exists()

    # update labels association by removing label_association_2
    AssociatedLabel.update_association(labels_data, alert_receive_channel, organization)
    assert len(alert_receive_channel.labels.all()) == 1
    assert alert_receive_channel.labels.filter(
        key=label_association_1.key_id, value=label_association_1.value_id
    ).exists()
    assert not alert_receive_channel.labels.filter(
        key=label_association_2.key_id, value=label_association_2.value_id
    ).exists()


@pytest.mark.django_db
def test_get_associating_label_model():
    model_name = AlertReceiveChannel.__name__
    expected_result = AlertReceiveChannelAssociatedLabel
    result = get_associating_label_model(model_name)
    assert result == expected_result

    model_name = Webhook.__name__
    expected_result = WebhookAssociatedLabel
    result = get_associating_label_model(model_name)
    assert result == expected_result

    wrong_model_name = "SomeModel"
    with pytest.raises(LookupError):
        get_associating_label_model(wrong_model_name)
