import pytest

from apps.alerts.models import AlertReceiveChannel
from apps.labels.models import AlertReceiveChannelAssociatedLabel, AssociatedLabel, LabelValueCache
from apps.labels.utils import get_associating_label_model


@pytest.mark.django_db
def test_label_associate_new_label(make_organization, make_alert_receive_channel):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    label_key_id = "testkeyid"
    label_value_id = "testvalueid"
    labels_data = [
        {
            "key": {"id": label_key_id, "name": "testkey"},
            "value": {"id": label_value_id, "name": "testvalue"},
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
            "key": {"id": label_key.id, "name": label_key.name},
            "value": {"id": label_value.id, "name": label_value.name},
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
            "key": {"id": label_association_1.key_id, "name": label_association_1.key.name},
            "value": {"id": label_association_1.value_id, "name": label_association_1.value.name},
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

    wrong_model_name = "SomeModel"
    with pytest.raises(LookupError):
        get_associating_label_model(wrong_model_name)
