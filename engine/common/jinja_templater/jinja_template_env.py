from django.utils import timezone
from jinja2 import BaseLoader
from jinja2.exceptions import SecurityError
from jinja2.sandbox import SandboxedEnvironment

from .filters import (
    datetimeformat,
    iso8601_to_time,
    json_dumps,
    regex_match,
    regex_replace,
    regex_search,
    to_pretty_json,
)


def raise_security_exception(name):
    raise SecurityError(f"use of '{name}' is restricted")


jinja_template_env = SandboxedEnvironment(loader=BaseLoader())

jinja_template_env.filters["datetimeformat"] = datetimeformat
jinja_template_env.filters["iso8601_to_time"] = iso8601_to_time
jinja_template_env.filters["tojson_pretty"] = to_pretty_json
jinja_template_env.globals["time"] = timezone.now
jinja_template_env.globals["range"] = lambda *args: raise_security_exception("range")
jinja_template_env.filters["regex_replace"] = regex_replace
jinja_template_env.filters["regex_match"] = regex_match
jinja_template_env.filters["regex_search"] = regex_search
jinja_template_env.filters["json_dumps"] = json_dumps
