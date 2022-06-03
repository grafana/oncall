from django.utils import timezone
from jinja2 import BaseLoader
from jinja2.sandbox import SandboxedEnvironment

from .filters import datetimeformat, iso8601_to_time, to_pretty_json

jinja_template_env = SandboxedEnvironment(loader=BaseLoader())

jinja_template_env.filters["datetimeformat"] = datetimeformat
jinja_template_env.filters["iso8601_to_time"] = iso8601_to_time
jinja_template_env.filters["tojson_pretty"] = to_pretty_json
jinja_template_env.globals["time"] = timezone.now
