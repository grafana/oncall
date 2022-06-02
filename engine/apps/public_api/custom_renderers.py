import json

from rest_framework.renderers import BaseRenderer


class CalendarRenderer(BaseRenderer):
    """
    A basic customer renderer to set the format to text to remove escape characters
    on feed requests.
    """

    media_type = "text/calendar"
    format = "txt"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, bytes):
            return data
        error_response = json.dumps(data)
        return bytes(error_response.encode("utf-8"))
