import logging
import typing

from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from apps.labels.client import LabelsAPIClient, LabelsRepoAPIException
from apps.labels.types import LabelOption, LabelPair
from apps.labels.utils import LABEL_OUTDATED_TIMEOUT_MINUTES, get_associating_label_model
from apps.user_management.models import Organization
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


class KVPair(typing.TypedDict):
    value_name: str
    key_name: str


def unify_labels_data(labels_data: typing.List[LabelOption] | LabelOption) -> typing.Dict[str, KVPair]:
    # Returns map of value id to value data.
    # Deprecated and left for backward compatibility.
    values_data: typing.Dict[str, KVPair]
    if isinstance(labels_data, list):  # LabelsData
        values_data = {
            label["value"]["id"]: {"value_name": label["value"]["name"], "key_name": label["key"]["name"]}
            for label in labels_data
        }
    else:  # LabelOption
        values_data = {
            value["id"]: {"value_name": value["name"], "key_name": labels_data["key"]["name"]}
            for value in labels_data["values"]
        }
    return values_data


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_labels_cache(labels_data: typing.List[LabelOption] | LabelOption):
    """
    1. Expects map of value_id -> value_name, key_name
    2. Fetches values filtered by map key
    3. Updates value and key if it's name different
    4. Updates value key name and updates if's name different
    Deprecated and left for backward compatibility.
    """
    from apps.labels.models import LabelKeyCache, LabelValueCache

    # this is a quick fix for tasks with wrong labels_data and can be removed later since handling this error happens in
    # the parent task now
    if isinstance(labels_data, dict) and labels_data.get("error"):
        return

    values_data: typing.Dict[str, KVPair] = unify_labels_data(labels_data)
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
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_label_option_cache(label_option: LabelOption):
    """
    update_label_cache updates cache for label's key, and it's every value
    """
    values_id_to_pair = {value["id"]: {"value": value, "key": label_option["key"]} for value in label_option["values"]}
    _update_labels_cache(values_id_to_pair)


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_label_pairs_cache(label_pairs: typing.List[LabelPair]):
    """
    update_label_pair updates cache for list of LabelPairs.
    """
    value_id_to_pair = {label["value"]["id"]: {"value": label["value"], "key": label["key"]} for label in label_pairs}
    _update_labels_cache(value_id_to_pair)


def _update_labels_cache(values_id_to_pair: typing.Dict[str, LabelPair]):
    """
    _update_labels_cache updates LabelKeyCache and LabelValueCache.
    It expects dict { value_id: [value_name, key_name] } and will fetch and update LabelKeyCache and LabelValueCache.
    """
    from apps.labels.models import LabelKeyCache, LabelValueCache

    values = LabelValueCache.objects.filter(id__in=values_id_to_pair).select_related("key")
    now = timezone.now()

    if not values:
        return

    keys_to_update = set()

    for value in values:
        value.name = values_id_to_pair[value.id]["value"]["name"]
        value.prescribed = values_id_to_pair[value.id]["value"]["prescribed"]
        value.last_synced = now

        value.key.name = values_id_to_pair[value.id]["key"]["name"]
        value.key.prescribed = values_id_to_pair[value.id]["key"]["prescribed"]
        value.key.last_synced = now
        keys_to_update.add(value.key)

    LabelKeyCache.objects.bulk_update(keys_to_update, fields=["name", "last_synced", "prescribed"])
    LabelValueCache.objects.bulk_update(values, fields=["name", "last_synced", "prescribed"])


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
        try:
            label_option, _ = client.get_label_by_key_id(key_id)
        except LabelsRepoAPIException as e:
            logger.warning(
                f"Error on get label data: organization: {organization_id}, key_id {key_id}, error: {e}, "
                f"error message: {e.msg}"
            )
            continue
        if label_option:
            update_label_option_cache.apply_async((label_option,))
