import logging

from jinja2.exceptions import SecurityError

from .jinja_template_env import jinja_template_env

logger = logging.getLogger(__name__)


class JinjaTemplateRenderException(Exception):
    def __init__(self, fallback_message):
        self.fallback_message = fallback_message


def apply_jinja_template(template, payload=None, raise_exception=False, **kwargs):
    try:
        #TODO: Add template size check
        compiled_template = jinja_template_env.from_string(template)
        return compiled_template.render(payload=payload, **kwargs)
    except Exception as e:
        if isinstance(e, SecurityError):
            logger.warning(f"SecurityError process template={template} payload={payload}")
        message = f"Error {str(e)}"
        if raise_exception:
            raise JinjaTemplateRenderException(message)
        return message
