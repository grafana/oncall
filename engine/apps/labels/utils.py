import typing

from django.apps import apps  # noqa: I251
from django.conf import settings

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup, AlertReceiveChannel
    from apps.labels.models import AssociatedLabel
    from apps.user_management.models import Organization


LABEL_OUTDATED_TIMEOUT_MINUTES = 30
ASSOCIATED_MODEL_NAME = "AssociatedLabel"


class LabelUpdateParam(typing.TypedDict):
    name: str


class LabelParams(typing.TypedDict):
    id: str
    name: str


class LabelData(typing.TypedDict):
    key: LabelParams
    value: LabelParams


class ValueData(typing.TypedDict):
    value_name: str
    key_name: str


class LabelKeyData(typing.TypedDict):
    key: LabelParams
    values: typing.List[LabelParams]


LabelsData = typing.List[LabelData]
LabelsKeysData = typing.List[LabelParams]


def get_associating_label_model(obj_model_name: str) -> typing.Type["AssociatedLabel"]:
    associating_label_model_name = obj_model_name + ASSOCIATED_MODEL_NAME
    label_model = apps.get_model("labels", associating_label_model_name)
    return label_model


def is_labels_feature_enabled(organization: "Organization") -> bool:
    return (
        settings.FEATURE_LABELS_ENABLED_FOR_ALL
        or organization.org_id in settings.FEATURE_LABELS_ENABLED_FOR_GRAFANA_ORGS  # Grafana org ID, not OnCall org ID
    )


def assign_labels(alert_group: "AlertGroup", alert_receive_channel: "AlertReceiveChannel") -> None:
    from apps.labels.models import AlertGroupAssociatedLabel

    if not is_labels_feature_enabled(alert_receive_channel.organization):
        return

    # inherit labels from the integration
    alert_group_labels = [
        AlertGroupAssociatedLabel(
            alert_group=alert_group,
            organization=alert_receive_channel.organization,
            key_name=label.key.name,
            value_name=label.value.name,
        )
        for label in alert_receive_channel.labels.filter(inheritable=True).select_related("key", "value")
    ]
    AlertGroupAssociatedLabel.objects.bulk_create(alert_group_labels)


def get_label_verbal(labelable) -> typing.Dict[str, str]:
    """
    label_verbal returns dict of labels' key and values names for the given object
    """
    return {label.key.name: label.value.name for label in labelable.labels.all().select_related("key", "value")}


def get_alert_group_label_verbal(alert_group: "AlertGroup") -> typing.Dict[str, str]:
    """
    get_alert_group_label_verbal returns dict of labels' key and values names for the given alert group.
    It's different from get_label_verbal, because AlertGroupAssociated labels store key/value_name, not key/value_id
    """
    return {label.key_name: label.value_name for label in alert_group.labels.all()}
