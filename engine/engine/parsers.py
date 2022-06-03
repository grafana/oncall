from django.conf import settings
from rest_framework import parsers, renderers


def check_content_length(parser_context):
    """Enforce DATA_UPLOAD_MAX_MEMORY_SIZE for json rest framework API requests."""
    if parser_context and settings.DATA_UPLOAD_MAX_MEMORY_SIZE and "request" in parser_context:
        try:
            content_length = int(parser_context["request"].META.get("CONTENT_LENGTH", 0))
        except (ValueError, TypeError):
            content_length = 0

        if content_length and content_length > settings.DATA_UPLOAD_MAX_MEMORY_SIZE or content_length < 0:
            raise parsers.ParseError("RequestDataTooBig")


class JSONParser(parsers.JSONParser):
    """
    Parse JSON-serialized data.
    Enforce django setting for DATA_UPLOAD_MAX_MEMORY_SIZE.
    """

    media_type = "application/json"
    renderer_class = renderers.JSONRenderer

    def parse(self, stream, media_type=None, parser_context=None):
        """Parse incoming bytestream as JSON and returns the resulting data."""
        # see https://github.com/encode/django-rest-framework/issues/4760
        check_content_length(parser_context)
        return super(JSONParser, self).parse(stream, media_type, parser_context)


class FormParser(parsers.FormParser):
    """
    Parse form data.
    Enforce django setting for DATA_UPLOAD_MAX_MEMORY_SIZE.
    """

    media_type = "application/x-www-form-urlencoded"

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Parses the incoming bytestream as a URL encoded form,
        and returns the resulting QueryDict.
        """
        # see https://github.com/encode/django-rest-framework/issues/4760
        check_content_length(parser_context)
        return super(FormParser, self).parse(stream, media_type, parser_context)
