import json
import logging
import typing

from apps.labels import types
from apps.labels.utils import is_labels_feature_enabled
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning

if typing.TYPE_CHECKING:
    from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel

logger = logging.getLogger(__name__)

# What can be used as a label key/value coming out from the template
LABEL_VALUE_TYPES = (str, int, float, bool)

# Maximum number of labels per alert group, excess labels will be dropped
MAX_LABELS_PER_ALERT_GROUP = 15


def gather_alert_labels(
    alert_receive_channel: "AlertReceiveChannel", raw_request_data: "Alert.RawRequestData"
) -> typing.Optional[types.AlertLabels]:
    """
    gather_alert_labels gathers labels for an alert received by the alert receive channel.
    1. static labels - inherits them from integration.
    2. dynamic labels and multi-label extraction template – templating the raw_request_data.
    """
    if not is_labels_feature_enabled(alert_receive_channel.organization):
        return None

    # apply static labels by inheriting labels from the integration
    labels = {
        label.key.name: label.value.name for label in alert_receive_channel.labels.all().select_related("key", "value")
    }

    labels.update(_apply_dynamic_labels(alert_receive_channel, raw_request_data))

    labels.update(_apply_multi_label_extraction_template(alert_receive_channel, raw_request_data))

    return labels


def save_alert_group_labels(
    alert_group: "AlertGroup", alert_receive_channel: "AlertReceiveChannel", labels: typing.Optional[types.AlertLabels]
) -> None:
    from apps.labels.models import AlertGroupAssociatedLabel

    if not is_labels_feature_enabled(alert_receive_channel.organization) or not labels:
        return

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

    # only keep up to MAX_LABELS_PER_ALERT_GROUP labels per alert group
    if len(alert_group_labels) > MAX_LABELS_PER_ALERT_GROUP:
        logger.warning(
            "Too many labels for alert group %s. Dropping %d labels.",
            alert_group.id,
            len(alert_group_labels) - MAX_LABELS_PER_ALERT_GROUP,
        )
        alert_group_labels = alert_group_labels[:MAX_LABELS_PER_ALERT_GROUP]

    # bulk create associated labels
    AlertGroupAssociatedLabel.objects.bulk_create(alert_group_labels)


def _apply_dynamic_labels(
    alert_receive_channel: "AlertReceiveChannel", raw_request_data: "Alert.RawRequestData"
) -> types.AlertLabels:
    from apps.labels.models import LabelKeyCache

    if alert_receive_channel.alert_group_labels_custom is None:
        return {}

    # fetch up-to-date label key names
    label_key_names = {
        k.id: k.name
        for k in LabelKeyCache.objects.filter(
            id__in=[label[0] for label in alert_receive_channel.alert_group_labels_custom]
        ).only("id", "name")
    }

    result_labels = {}
    for label in alert_receive_channel.alert_group_labels_custom:
        label = _apply_dynamic_label_entry(label, label_key_names, raw_request_data)
        if label:
            key, value = label
            result_labels[key] = value

    return result_labels


def _apply_dynamic_label_entry(
    label: "AlertReceiveChannel.DynamicLabelsEntryDB", keys: dict, payload: "Alert.RawRequestData"
) -> typing.Optional[tuple[str, str]]:
    key_id, value_id, template = label
    key, value = "", ""

    # check if key exists
    if key_id in keys:
        key = keys[key_id]
    else:
        logger.warning("Label key cache not found. %s", key_id)
        return None

    if value_id:
        # if value_id is present - it's a static k-v pair. Deprecated.
        logger.warning(
            "value_id is present in dynamic label entry. It's deprecated & should not be there. %s", value_id
        )
    elif template:
        # otherwise, it's a key-template pair, applying template
        try:
            value = apply_jinja_template(template, payload)
        except (JinjaTemplateError, JinjaTemplateWarning) as e:
            logger.warning("Failed to apply template. %s", e.fallback_message)
            return None
        if not _validate_templated_value(value):
            return None
    else:
        logger.warning("Label value is neither a value_id, nor a template. %s", key)
    return key, value


def _apply_multi_label_extraction_template(
    alert_receive_channel: "AlertReceiveChannel", raw_request_data: "Alert.RawRequestData"
) -> types.AlertLabels:
    from apps.labels.models import MAX_KEY_NAME_LENGTH

    if not alert_receive_channel.alert_group_labels_template:
        return {}

    # render template - output will be a string.
    # It's expected that it will be a JSON string, to be parsed into a dict.
    try:
        rendered_labels = apply_jinja_template(alert_receive_channel.alert_group_labels_template, raw_request_data)
    except (JinjaTemplateError, JinjaTemplateWarning) as e:
        logger.warning("Failed to apply template. %s", e.fallback_message)
        return {}

    # unmarshal rendered_labels JSON string to dict
    try:
        labels_dict = json.loads(rendered_labels)
    except (TypeError, json.JSONDecodeError):
        # it's expected, if user misconfigured the template
        logger.warning("Failed to parse template result. %s", rendered_labels)
        return {}

    if not isinstance(labels_dict, dict):
        logger.warning("Template result is not a dict. %s", labels_dict)
        return {}

    # validate dict of labels, drop invalid keys & values, convert all values to strings
    result_labels = {}
    for key in labels_dict:
        # check key length
        if len(key) == 0:
            logger.warning("Template result key is empty. %s", key)
            continue

        if len(key) > MAX_KEY_NAME_LENGTH:
            logger.warning("Template result key is too long. %s", key)
            continue

        # Checks specific to multi-label extraction template, because we're receiving value from a JSON:
        # 1. check type
        # 2. convert back to string
        if not isinstance(labels_dict[key], LABEL_VALUE_TYPES):
            logger.warning("Templated value has invalid type. %s", labels_dict[key])
            continue
        value = str(labels_dict[key])

        # apply common value checks
        if not _validate_templated_value(value):
            continue

        result_labels[key] = labels_dict[key]

    return result_labels


def _validate_templated_value(value: str) -> bool:
    from apps.labels.models import MAX_VALUE_NAME_LENGTH

    # check value length
    if len(value) == 0:
        logger.warning("Templated value value is empty. %s", value)
        return False

    if len(value) > MAX_VALUE_NAME_LENGTH:
        logger.warning("Templated value is too long. %s", value)
        return False

    if value.lower().strip() == "none":
        logger.warning("Templated value is None. %s", value)
        return False
    return True
