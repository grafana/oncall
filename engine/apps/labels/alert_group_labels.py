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


def gather_labels_from_alert_receive_channel_and_raw_request_data(
    alert_receive_channel: "AlertReceiveChannel", raw_request_data: "Alert.RawRequestData"
) -> typing.Optional[types.AlertLabels]:
    if not is_labels_feature_enabled(alert_receive_channel.organization):
        return None

    # apply static labels by inheriting labels from the integration
    labels = {
        label.key.name: label.value.name for label in alert_receive_channel.labels.all().select_related("key", "value")
    }

    labels.update(_apply_dynamic_labels(alert_receive_channel, raw_request_data))

    labels.update(_apply_multi_label_extraction_template(alert_receive_channel, raw_request_data))

    return labels


def assign_labels(
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
    from apps.labels.models import LabelKeyCache, LabelValueCache

    if alert_receive_channel.alert_group_labels_custom is None:
        return {}

    # fetch up-to-date label key names
    label_key_names = {
        k.id: k.name
        for k in LabelKeyCache.objects.filter(
            id__in=[label[0] for label in alert_receive_channel.alert_group_labels_custom]
        ).only("id", "name")
    }

    # fetch up-to-date label value names
    label_value_names = {
        v.id: v.name
        for v in LabelValueCache.objects.filter(
            id__in=[label[1] for label in alert_receive_channel.alert_group_labels_custom if label[1]]
        ).only("id", "name")
    }

    result_labels = {}
    for label in alert_receive_channel.alert_group_labels_custom:
        label = _apply_dynamic_label_entry(label, label_key_names, label_value_names, raw_request_data)
        if label:
            key, value = label
            result_labels[key] = value

    return result_labels


def _apply_dynamic_label_entry(
    label: "AlertReceiveChannel.LabelsSchemaEntryDB", keys, values, payload
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

    try:
        rendered = apply_jinja_template(alert_receive_channel.alert_group_labels_template, raw_request_data)
    except (JinjaTemplateError, JinjaTemplateWarning) as e:
        logger.warning("Failed to apply template. %s", e.fallback_message)
        return {}

    try:
        rendered_labels = json.loads(rendered)
    except (TypeError, json.JSONDecodeError):
        logger.warning("Failed to parse template result. %s", rendered)
        return {}

    if not isinstance(rendered_labels, dict):
        logger.warning("Template result is not a dict. %s", rendered_labels)
        return {}

    # validate rendered k-v pairs & drop invalid ones
    for key in rendered_labels:
        # check key length
        if len(key) == 0:
            logger.warning("Template result key is empty. %s", key)
            del rendered_labels[key]
            continue

        if len(key) > MAX_KEY_NAME_LENGTH:
            logger.warning("Template result key is too long. %s", key)
            del rendered_labels[key]
            continue

        if not _validate_templated_value(rendered_labels[key]):
            del rendered_labels[key]
            continue

    return rendered_labels


def _validate_templated_value(value: typing.Any) -> bool:
    from apps.labels.models import MAX_VALUE_NAME_LENGTH

    # check value type
    if not isinstance(value, LABEL_VALUE_TYPES):
        logger.warning("Templated value has invalid type. %s", value)
        return False

    # convert value to string
    value = str(value)

    # check value length
    if len(value) == 0:
        logger.warning("Templated value value is empty. %s", value)
        return False

    if len(value) > MAX_VALUE_NAME_LENGTH:
        logger.warning("Templated value is too long. %s", value)
        return False
    return True
