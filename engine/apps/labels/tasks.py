import typing

from django.conf import settings
from django.utils import timezone

from apps.labels.client import LabelsAPIClient
from apps.labels.utils import LABEL_OUTDATED_TIMEOUT_MINUTES
from apps.user_management.models import Organization
from common.custom_celery_tasks import shared_dedicated_queue_retry_task

if typing.TYPE_CHECKING:
    from apps.labels.models import LabelKeyData, LabelsData


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_labels_cache_for_key(label_data: "LabelKeyData"):
    from apps.labels.models import LabelKeyCache, LabelValueCache

    # {
    #  	"key":{"id":"746982e688e3","repr":"severity"},
    #   "values":[{"id":"106a01295d2f","repr":"critical"}, {"id":"8c77ce0e8a77","repr":"warning"}]
    # }
    label_key = LabelKeyCache.objects.filter(id=label_data["key"]["id"]).first()
    if not label_key:
        # there is no associations with this key
        return

    now = timezone.now()
    label_key.repr = label_data["key"]["repr"]
    label_key.save(update_fields=["repr"])

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

    # [{"key":{"id":"746982e688e3","repr":"severity"}, "value":{"id":"106a01295d2f","repr":"critical"}}]
    now = timezone.now()
    values_data = {
        label["value"]["id"]: {"value_repr": label["value"]["repr"], "key_repr": label["key"]["repr"]}
        for label in labels_data
    }
    outdated_last_synced = now - timezone.timedelta(minutes=LABEL_OUTDATED_TIMEOUT_MINUTES)
    values = LabelValueCache.objects.filter(id__in=values_data, last_synced__lte=outdated_last_synced).select_related(
        "key"
    )

    if not values:
        return

    keys_to_update = set()

    for value in values:
        if value.repr != values_data[value.id]["value_repr"]:
            value.repr = values_data[value.id]["value_repr"]
        value.last_synced = now

        if value.key.repr != values_data[value.id]["key_repr"]:
            value.repr = values_data[value.id]["key_repr"]
        value.key.last_synced = now
        keys_to_update.add(value.key)

    LabelKeyCache.objects.bulk_update(keys_to_update, fields=["repr", "last_synced"])
    LabelValueCache.objects.bulk_update(values, fields=["repr", "last_synced"])


@shared_dedicated_queue_retry_task(
    autoretry_for=(Exception,), retry_backoff=True, max_retries=1 if settings.DEBUG else None
)
def update_instances_labels_cache(organization_id, instance_ids, instance_model_name):
    from apps.labels.models import LabelValueCache, get_associating_label_model

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
            update_labels_cache_for_key.apply_async(label_data)
