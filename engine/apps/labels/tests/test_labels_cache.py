from unittest.mock import call, patch

import pytest
from django.utils import timezone

from apps.labels.models import LabelKeyCache, LabelValueCache
from apps.labels.tasks import update_instances_labels_cache, update_labels_cache
from apps.labels.utils import LABEL_OUTDATED_TIMEOUT_MINUTES


@pytest.mark.django_db
def test_update_labels_cache_for_key(make_organization, make_label_key_and_value, make_label_value):
    organization = make_organization()
    label_key, label_value1 = make_label_key_and_value(organization)
    label_value2 = make_label_value(label_key)
    new_key_repr = "updatekeyrepr"
    new_value1_repr = "updatevalue1repr"
    old_value2_repr = label_value2.repr
    last_synced = label_key.last_synced

    label_data = {
        "key": {"id": label_key.id, "repr": new_key_repr},
        "values": [{"id": label_value1.id, "repr": new_value1_repr}, {"id": label_value2.id, "repr": old_value2_repr}],
    }
    assert label_key.repr != new_key_repr
    assert label_value1.repr != new_value1_repr

    update_labels_cache(label_data)

    label_key.refresh_from_db()
    label_value1.refresh_from_db()
    label_value2.refresh_from_db()

    for label_cache in (label_key, label_value1, label_value2):
        assert label_cache.last_synced > last_synced

    assert label_key.repr == new_key_repr
    assert label_value1.repr == new_value1_repr
    assert label_value2.repr == old_value2_repr


@pytest.mark.django_db
def test_update_labels_cache(make_organization, make_label_key_and_value, make_label_value):
    organization = make_organization()

    label_key1, label_value1_1 = make_label_key_and_value(organization)
    label_key2, label_value2_1 = make_label_key_and_value(organization)
    label_value2_2 = make_label_value(label_key2)
    new_key1_repr = "updatekey1repr"
    new_value1_1_repr = "updatevalue11repr"
    old_key2_repr = label_key2.repr
    old_value2_1_repr = label_value2_1.repr
    new_value2_2_repr = "updatevalue22repr"
    last_synced = label_key1.last_synced

    labels_data = [
        {
            "key": {"id": label_key1.id, "repr": new_key1_repr},
            "value": {"id": label_value1_1.id, "repr": new_value1_1_repr},
        },
        {
            "key": {"id": label_key2.id, "repr": old_key2_repr},
            "value": {"id": label_value2_1.id, "repr": old_value2_1_repr},
        },
        {
            "key": {"id": label_key2.id, "repr": old_key2_repr},
            "value": {"id": label_value2_2.id, "repr": new_value2_2_repr},
        },
    ]

    assert label_key1.repr != new_key1_repr
    assert label_value1_1.repr != new_value1_1_repr
    assert label_value2_2.repr != new_value2_2_repr

    update_labels_cache(labels_data)

    for label_cache in (label_key1, label_key2, label_value1_1, label_value2_1, label_value2_2):
        label_cache.refresh_from_db()
        assert label_cache.last_synced > last_synced

    assert label_key1.repr == new_key1_repr
    assert label_value1_1.repr == new_value1_1_repr

    assert label_key2.repr == old_key2_repr
    assert label_value2_1.repr == old_value2_1_repr
    assert label_value2_2.repr == new_value2_2_repr


@pytest.mark.django_db
def test_update_instances_labels_cache_recently_synced(
    make_organization, make_alert_receive_channel, make_integration_label_association
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    label_association = make_integration_label_association(organization, alert_receive_channel)

    assert not label_association.key.is_outdated
    assert not label_association.value.is_outdated

    with patch("apps.labels.client.LabelsAPIClient.get_values") as mock_get_values:
        with patch("apps.labels.tasks.update_labels_cache.apply_async") as mock_update_cache:
            update_instances_labels_cache(
                organization.id, [alert_receive_channel.id], alert_receive_channel._meta.model.__name__
            )
    assert not mock_get_values.called
    assert not mock_update_cache.called


@pytest.mark.django_db
def test_update_instances_labels_cache_outdated(
    make_organization, make_alert_receive_channel, make_integration_label_association
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    label_association = make_integration_label_association(organization, alert_receive_channel)
    outdated_last_synced = timezone.now() - timezone.timedelta(minutes=LABEL_OUTDATED_TIMEOUT_MINUTES + 1)

    LabelKeyCache.objects.filter(id=label_association.key_id).update(last_synced=outdated_last_synced)
    LabelValueCache.objects.filter(id=label_association.value_id).update(last_synced=outdated_last_synced)
    label_association.refresh_from_db()
    assert label_association.key.is_outdated
    assert label_association.value.is_outdated

    label_data = {
        "key": {"id": label_association.key.id, "repr": label_association.key.repr},
        "values": [{"id": label_association.value.id, "repr": label_association.value.repr}],
    }

    with patch("apps.labels.client.LabelsAPIClient.get_values", return_value=(label_data, None)) as mock_get_values:
        with patch("apps.labels.tasks.update_labels_cache.apply_async") as mock_update_cache:
            update_instances_labels_cache(
                organization.id, [alert_receive_channel.id], alert_receive_channel._meta.model.__name__
            )
    assert mock_get_values.called
    assert mock_update_cache.called
    assert mock_update_cache.call_args == call((label_data,))
