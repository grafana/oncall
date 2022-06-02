from rest_framework import renderers


class PlainTextRenderer(renderers.BaseRenderer):
    media_type = "text/plain"

    def render(self, data, media_type=None, renderer_context=None):
        if type(data) == dict:
            result = ""
            for k, v in data.items():
                result += f"{k}: {v}\n"
            return result
        return data.encode(self.charset)
