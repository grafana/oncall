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

    # inherit labels from the integration
    labels = {
        label.key.name: label.value.name
        for label in alert_receive_channel.labels.filter(inheritable=True).select_related("key", "value")
    }

    # apply custom labels
    labels.update(_custom_labels(alert_receive_channel, raw_request_data))

    # apply template labels
    labels.update(_template_labels(alert_receive_channel, raw_request_data))

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


def _custom_labels(
    alert_receive_channel: "AlertReceiveChannel", raw_request_data: "Alert.RawRequestData"
) -> types.AlertLabels:
    from apps.labels.models import MAX_VALUE_NAME_LENGTH, LabelKeyCache, LabelValueCache

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

    rendered_labels = {}
    for label in alert_receive_channel.alert_group_labels_custom:
        key_id, value_id, template = label

        if key_id in label_key_names:
            key = label_key_names[key_id]
        else:
            logger.warning("Label key cache not found. %s", key_id)
            continue

        if value_id:
            if value_id in label_value_names:
                rendered_labels[key] = label_value_names[value_id]
            else:
                logger.warning("Label value cache not found. %s", value_id)
                continue
        else:
            try:
                rendered_labels[key] = apply_jinja_template(template, raw_request_data)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                logger.warning("Failed to apply template. %s", e.fallback_message)
                continue

    labels = {}
    for key in rendered_labels:
        value = rendered_labels[key]

        # check value length
        if len(value) == 0:
            logger.warning("Template result value is empty. %s", value)
            continue

        if len(value) > MAX_VALUE_NAME_LENGTH:
            logger.warning("Template result value is too long. %s", value)
            continue

        labels[key] = value

    return labels


def _template_labels(
    alert_receive_channel: "AlertReceiveChannel", raw_request_data: "Alert.RawRequestData"
) -> types.AlertLabels:
    from apps.labels.models import MAX_KEY_NAME_LENGTH, MAX_VALUE_NAME_LENGTH

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

    labels = {}
    for key in rendered_labels:
        value = rendered_labels[key]

        # check value type
        if not isinstance(value, LABEL_VALUE_TYPES):
            logger.warning("Template result value has invalid type. %s", value)
            continue

        # convert value to string
        value = str(value)

        # check key length
        if len(key) == 0:
            logger.warning("Template result key is empty. %s", key)
            continue

        if len(key) > MAX_KEY_NAME_LENGTH:
            logger.warning("Template result key is too long. %s", key)
            continue

        # check value length
        if len(value) == 0:
            logger.warning("Template result value is empty. %s", value)
            continue

        if len(value) > MAX_VALUE_NAME_LENGTH:
            logger.warning("Template result value is too long. %s", value)
            continue

        labels[key] = value

    return labels
