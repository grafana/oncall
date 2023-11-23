import json
import logging
import typing

from django.apps import apps  # noqa: I251
from django.conf import settings

from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning, apply_jinja_template

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup, AlertReceiveChannel
    from apps.labels.models import AssociatedLabel
    from apps.user_management.models import Organization

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


def assign_labels(
    alert_group: "AlertGroup", alert_receive_channel: "AlertReceiveChannel", raw_request_data: typing.Any
) -> None:
    from apps.labels.models import AlertGroupAssociatedLabel

    if not is_labels_feature_enabled(alert_receive_channel.organization):
        return

    # inherit labels from the integration
    labels = {
        label.key.name: label.value.name
        for label in alert_receive_channel.labels.filter(inheritable=True).select_related("key", "value")
    }

    # apply custom labels
    labels.update(_custom_labels(alert_receive_channel, raw_request_data))

    # apply template labels
    labels.update(_template_labels(alert_receive_channel, raw_request_data))

    # create associated labels
    alert_group_labels = [
        AlertGroupAssociatedLabel(
            alert_group=alert_group,
            organization=alert_receive_channel.organization,
            key_name=key,
            value_name=value,
        )
        for key, value in labels.items()
    ]
    # sort associated labels by key and value
    alert_group_labels.sort(key=lambda label: (label.key_name, label.value_name))
    # bulk create associated labels
    AlertGroupAssociatedLabel.objects.bulk_create(alert_group_labels)


def _custom_labels(alert_receive_channel: "AlertReceiveChannel", raw_request_data: typing.Any) -> dict[str, str]:
    # TODO: implement label key/value name updates, refactor

    from apps.labels.models import LabelKeyCache, LabelValueCache

    label_key_ids = [label["key"]["id"] for label in alert_receive_channel.alert_group_labels_custom]
    label_key_names = {k.id: k.name for k in LabelKeyCache.objects.filter(id__in=label_key_ids).only("id", "name")}

    label_value_ids = [
        label["value"]["id"] for label in alert_receive_channel.alert_group_labels_custom if label["value"]["id"]
    ]
    label_value_names = {
        v.id: v.name for v in LabelValueCache.objects.filter(id__in=label_value_ids).only("id", "name")
    }

    labels = {}
    for label in alert_receive_channel.alert_group_labels_custom:
        key_name = label_key_names.get(label["key"]["id"], label["key"]["name"])
        value_name = (
            label_value_names.get(label["value"]["id"], label["value"]["name"])
            if label["value"]["id"]
            else label["value"]["name"]
        )

        if label["value"]["id"]:
            labels[key_name] = value_name
        else:
            try:
                labels[key_name] = apply_jinja_template(value_name, raw_request_data)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                logger.warning("Failed to apply template. %s", e.fallback_message)
                continue

    return labels


def _template_labels(alert_receive_channel: "AlertReceiveChannel", raw_request_data: typing.Any) -> dict[str, str]:
    if not alert_receive_channel.alert_group_labels_template:
        return {}

    try:
        rendered = apply_jinja_template(alert_receive_channel.alert_group_labels_template, raw_request_data)
    except (JinjaTemplateError, JinjaTemplateWarning) as e:
        logger.warning("Failed to apply template. %s", e.fallback_message)
        return {}

    try:
        labels = json.loads(rendered)
    except (TypeError, json.JSONDecodeError):
        logger.warning("Failed to parse template result. %s", rendered)
        return {}

    if not isinstance(labels, dict):
        logger.warning("Template result is not a dict. %s", labels)
        return {}

    # only keep labels with string, int, float, bool values
    return {str(k): str(v) for k, v in labels.items() if isinstance(v, (str, int, float, bool))}


def get_label_verbal(obj: typing.Any) -> dict[str, str]:
    return {label.key.name: label.value.name for label in obj.labels.all().select_related("key", "value")}


def get_alert_group_label_verbal(alert_group: "AlertGroup") -> dict[str, str]:
    """This is different from get_label_verbal because alert group labels store key/value names, not IDs"""
    return {label.key_name: label.value_name for label in alert_group.labels.all()}
