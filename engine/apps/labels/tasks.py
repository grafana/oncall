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


class ValueData(typing.TypedDict):
    value_name: str
    key_name: str


def unify_labels_data(labels_data: LabelsData | LabelKeyData) -> typing.Dict[str, ValueData]:
    values_data: typing.Dict[str, ValueData]
    if isinstance(labels_data, list):  # LabelsData
        values_data = {
            label["value"]["id"]: {"value_name": label["value"]["name"], "key_name": label["key"]["name"]}
            for label in labels_data
        }
    else:  # LabelKeyData
        values_data = {
            label["id"]: {"value_name": label["name"], "key_name": labels_data["key"]["name"]}
            for label in labels_data["values"]
        }
    return values_data


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_labels_cache(labels_data: LabelsData | LabelKeyData):
    from apps.labels.models import LabelKeyCache, LabelValueCache

    values_data: typing.Dict[str, ValueData] = unify_labels_data(labels_data)
    values = LabelValueCache.objects.filter(id__in=values_data).select_related("key")
    now = timezone.now()

    if not values:
        return

    keys_to_update = set()

    for value in values:
        if value.name != values_data[value.id]["value_name"]:
            value.name = values_data[value.id]["value_name"]
        value.last_synced = now

        if value.key.name != values_data[value.id]["key_name"]:
            value.key.name = values_data[value.id]["key_name"]
        value.key.last_synced = now
        keys_to_update.add(value.key)

    LabelKeyCache.objects.bulk_update(keys_to_update, fields=["name", "last_synced"])
    LabelValueCache.objects.bulk_update(values, fields=["name", "last_synced"])


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else 10
)
def update_instances_labels_cache(organization_id: int, instance_ids: typing.List[int], instance_model_name: str):
    from apps.labels.models import LabelValueCache

    now = timezone.now()
    organization = Organization.objects.get(id=organization_id)

    model = get_associating_label_model(instance_model_name)
    field_name = model.get_associating_label_field_name()
    associated_instances = {f"{field_name}_id__in": instance_ids}
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
            update_labels_cache.apply_async((label_data,))
