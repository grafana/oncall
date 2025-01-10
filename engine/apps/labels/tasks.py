import logging
import typing

from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from apps.labels.client import LabelsAPIClient, LabelsRepoAPIException
from apps.labels.types import LabelOption, LabelPair
from apps.labels.utils import LABEL_OUTDATED_TIMEOUT_MINUTES, get_associating_label_model
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)

MAX_RETRIES = 1 if settings.DEBUG else 10


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


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def update_instances_labels_cache(organization_id: int, instance_ids: typing.List[int], instance_model_name: str):
    from apps.labels.models import LabelValueCache
    from apps.user_management.models import Organization

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


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def add_service_label_for_alerting_integrations():
    """
    This task should be called manually and only once.
    Starts tasks that add `service_name` dynamic label for Alerting integrations
    """

    from apps.alerts.models import AlertReceiveChannel

    organization_ids = (
        AlertReceiveChannel.objects.filter(
            integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
            organization__is_grafana_labels_enabled=True,
            organization__deleted_at__isnull=True,
        )
        .values_list("organization", flat=True)
        .distinct()
    )

    for idx, organization_id in enumerate(organization_ids):
        countdown = idx // 10
        add_service_label_per_org.apply_async((organization_id,), countdown=countdown)


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def add_service_label_per_org(organization_id: int):
    """Add `service_name` dynamic label for all Alerting integrations per organization"""

    from apps.alerts.models import AlertReceiveChannel
    from apps.user_management.models import Organization

    organization = Organization.objects.get(id=organization_id)
    service_label_custom = AlertReceiveChannel._build_service_name_label_custom(organization)
    if not service_label_custom:
        return
    integrations = AlertReceiveChannel.objects.filter(
        integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        organization=organization,
    )
    integrations_to_update = []
    # add service label to integration custom labels if it's not already there
    for integration in integrations:
        dynamic_service_label_exists = False
        dynamic_labels = integration.alert_group_labels_custom if integration.alert_group_labels_custom else []
        for label in dynamic_labels:
            if label[0] == service_label_custom[0]:
                dynamic_service_label_exists = True
                break
        if dynamic_service_label_exists:
            continue
        integration.alert_group_labels_custom = [service_label_custom] + dynamic_labels
        integrations_to_update.append(integration)

    AlertReceiveChannel.objects.bulk_update(integrations_to_update, fields=["alert_group_labels_custom"])


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), retry_backoff=True, max_retries=MAX_RETRIES)
def add_service_label_for_integration(alert_receive_channel_id: int):
    """Add `service_name` dynamic label for Alerting integration"""

    from apps.alerts.models import AlertReceiveChannel

    alert_receive_channel = AlertReceiveChannel.objects.get(id=alert_receive_channel_id)
    alert_receive_channel.create_service_name_dynamic_label(True)
