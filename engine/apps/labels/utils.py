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

    # inherit all labels from the integration
    # FIXME: this is a temporary solution before we have a UI for configuring inherited labels
    alert_group_labels = [
        AlertGroupAssociatedLabel(
            alert_group=alert_group,
            organization=alert_receive_channel.organization,
            key_name=label.key.name,
            value_name=label.value.name,
        )
        for label in alert_receive_channel.labels.all().select_related("key", "value")
    ]
    AlertGroupAssociatedLabel.objects.bulk_create(alert_group_labels)
