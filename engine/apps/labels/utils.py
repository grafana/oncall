import logging
import typing

from django.apps import apps  # noqa: I251
from django.conf import settings

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


def get_associating_label_model(obj_model_name):
    associating_label_model_name = obj_model_name + ASSOCIATED_MODEL_NAME
    label_model = apps.get_model("labels", associating_label_model_name)
    return label_model


def is_labels_enabled(organization):
    """
    is_labels_enabled checks if oncall is deployed on same cluster that its grafana instance.
    Replace with feature flag when cross cluster requests are available for labels plugin
    """
    logger.info(
        "is_labels_enabled: "
        f"FEATURE_LABELS_ENABLED={settings.FEATURE_LABELS_ENABLED} "
        f"ONCALL_BACKEND_REGION={settings.ONCALL_BACKEND_REGION} "
        f"cluster_slug={organization.cluster_slug}"
    )
    # return settings.FEATURE_LABELS_ENABLED and settings.ONCALL_BACKEND_REGION == organization.cluster_slug
    return True  # todo
