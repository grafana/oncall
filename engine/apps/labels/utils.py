import logging
import typing

from django.apps import apps  # noqa: I251
from django.conf import settings

if typing.TYPE_CHECKING:
    from apps.labels.models import AssociatedLabel

logger = logging.getLogger(__name__)

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


def is_labels_feature_enabled(organization) -> bool:
    """
    Checks if labels feature enabled for all organizations (FEATURE_LABELS_ENABLED_FOR_ALL).
    If not, checks if current organization's grafana org_id is in the list of organizations labels feature enabled for
    (FEATURE_LABELS_ENABLED_FOR_GRAFANA_ORGS)
    """
    logger.info(
        "is_labels_feature_enabled: "
        f"FEATURE_LABELS_ENABLED_FOR_ALL={settings.FEATURE_LABELS_ENABLED_FOR_ALL}, "
        f"organization in FEATURE_LABELS_ENABLED_FOR_GRAFANA_ORGS="
        f"{organization.id in settings.FEATURE_LABELS_ENABLED_FOR_GRAFANA_ORGS}, "
        f"organization={organization.id}"
    )
    if not settings.FEATURE_LABELS_ENABLED_FOR_ALL:
        return organization.org_id in settings.FEATURE_LABELS_ENABLED_FOR_GRAFANA_ORGS
    return settings.FEATURE_LABELS_ENABLED_FOR_ALL
