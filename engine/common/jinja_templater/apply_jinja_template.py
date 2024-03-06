import logging
import typing

from django.conf import settings
from jinja2 import TemplateAssertionError, TemplateSyntaxError, UndefinedError
from jinja2.exceptions import SecurityError

from .jinja_template_env import jinja_template_env

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from apps.alerts.models import Alert
    from apps.labels.types import AlertLabels


class JinjaTemplateError(Exception):
    def __init__(self, fallback_message):
        self.fallback_message = f"Template Error: {fallback_message}"


class JinjaTemplateWarning(Exception):
    def __init__(self, fallback_message):
        self.fallback_message = f"Template Warning: {fallback_message}"


def apply_jinja_template(
    template: str,
    payload: typing.Optional["Alert.RawRequestData"] = None,
    result_length_limit=settings.JINJA_RESULT_MAX_LENGTH,
    **kwargs,
) -> str:
    if len(template) > settings.JINJA_TEMPLATE_MAX_LENGTH:
        raise JinjaTemplateError(
            f"Template exceeds length limit ({len(template)} > {settings.JINJA_TEMPLATE_MAX_LENGTH})"
        )

    try:
        compiled_template = jinja_template_env.from_string(template)
        result = compiled_template.render(payload=payload, **kwargs)
    except SecurityError as e:
        logger.warning(f"SecurityError process template={template} payload={payload}")
        raise JinjaTemplateError(str(e))
    except (TemplateAssertionError, TemplateSyntaxError) as e:
        raise JinjaTemplateError(str(e))
    except (TypeError, KeyError, ValueError, UndefinedError) as e:
        raise JinjaTemplateWarning(str(e))
    except Exception as e:
        logger.error(f"Unexpected template error: {str(e)} template={template} payload={payload}")
        raise JinjaTemplateError(str(e))

    return (result[:result_length_limit] + "..") if len(result) > result_length_limit else result


def apply_jinja_template_to_alert_payload_and_labels(
    template: str, payload: typing.Optional["Alert.RawRequestData"], labels: typing.Optional["AlertLabels"]
) -> str:
    return apply_jinja_template(template, payload=payload, labels=labels)


def templated_value_is_truthy(value: typing.Optional[str]) -> bool:
    if not isinstance(value, str):
        return False
    return value.strip().lower() in ["1", "true", "ok"]
