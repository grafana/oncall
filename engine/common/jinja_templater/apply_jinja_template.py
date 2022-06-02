from jinja2 import TemplateSyntaxError, UndefinedError

from .jinja_template_env import jinja_template_env


def apply_jinja_template(template, payload=None, **kwargs):
    try:
        template = jinja_template_env.from_string(template)
        result = template.render(payload=payload, **kwargs)
        return result, True
    except (UndefinedError, TypeError, ValueError, KeyError, TemplateSyntaxError):
        return None, False
