import logging
import typing

from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from apps.labels.client import LabelsAPIClient
from apps.labels.utils import LABEL_OUTDATED_TIMEOUT_MINUTES, LabelKeyData, LabelsData, get_associating_label_model
from apps.user_management.models import Organization
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_labels_cache_for_key(label_data: "LabelKeyData"):
    from apps.labels.models import LabelKeyCache, LabelValueCache

    label_key = LabelKeyCache.objects.filter(id=label_data["key"]["id"]).first()
    if not label_key:
        # there is no associations with this key
        return

    now = timezone.now()
    label_key.repr = label_data["key"]["repr"]
    label_key.save(update_fields=["repr", "last_synced"])

    values_data = {v["id"]: v["repr"] for v in label_data["values"]}

    label_values = label_key.values.all()
    for label_value in label_values:
        if label_value.repr != values_data[label_value.id]:
            label_value.repr = values_data[label_value.id]
        label_value.last_synced = now
    LabelValueCache.objects.bulk_update(label_values, fields=["repr", "last_synced"], batch_size=5000)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_labels_cache(labels_data: "LabelsData"):
    from apps.labels.models import LabelKeyCache, LabelValueCache

    now = timezone.now()
    values_data = {
        label["value"]["id"]: {"value_repr": label["value"]["repr"], "key_repr": label["key"]["repr"]}
        for label in labels_data
    }
    values = LabelValueCache.objects.filter(id__in=values_data).select_related("key")

    if not values:
        return

    keys_to_update = set()

    for value in values:
        if value.repr != values_data[value.id]["value_repr"]:
            value.repr = values_data[value.id]["value_repr"]
        value.last_synced = now

        if value.key.repr != values_data[value.id]["key_repr"]:
            value.key.repr = values_data[value.id]["key_repr"]
        value.key.last_synced = now
        keys_to_update.add(value.key)

    LabelKeyCache.objects.bulk_update(keys_to_update, fields=["repr", "last_synced"])
    LabelValueCache.objects.bulk_update(values, fields=["repr", "last_synced"])


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_instances_labels_cache(organization_id: int, instance_ids: typing.List[int], instance_model_name: str):
    from apps.labels.models import LabelValueCache

    now = timezone.now()
    model = get_associating_label_model(instance_model_name)
    organization = Organization.objects.get(id=organization_id)
    associated_instances = {f"{model.associated_instance_field}_id__in": instance_ids}
    values_ids = model.objects.filter(**associated_instances).values_list("value_id", flat=True)
    outdated_last_synced = now - timezone.timedelta(minutes=LABEL_OUTDATED_TIMEOUT_MINUTES)
    values = LabelValueCache.objects.filter(id__in=values_ids, last_synced__lte=outdated_last_synced)

    if not values:
        return

    keys_ids = set(value.key_id for value in values)

    client = LabelsAPIClient(organization.grafana_url, organization.api_token)
    for key_id in keys_ids:
        label_data, _ = client.get_values(key_id)
        if label_data:
            update_labels_cache_for_key.apply_async((label_data,))
