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
    repr: str


class LabelParams(typing.TypedDict):
    id: str
    repr: str


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
    # check FEATURE_LABELS_ENABLED in settings
    # checking labels feature flag per organization will be added later

    logger.info(
        "is_labels_feature_enabled: "
        f"FEATURE_LABELS_ENABLED={settings.FEATURE_LABELS_ENABLED} "
        f"organization={organization.id}"
    )
    return settings.FEATURE_LABELS_ENABLED
