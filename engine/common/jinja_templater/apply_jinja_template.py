from .jinja_template_env import jinja_template_env


class JinjaTemplateRenderException(Exception):
    def __init__(self, fallback_message):
        self.fallback_message = fallback_message


def apply_jinja_template(template, payload=None, raise_exception=False, **kwargs):
    try:
        template = jinja_template_env.from_string(template)
        return template.render(payload=payload, **kwargs)
    except Exception as e:
        message = f"Error {str(e)}"
        if raise_exception:
            raise JinjaTemplateRenderException(message)
        return message
