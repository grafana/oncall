import json

from django.conf import settings
from django.http import HttpResponse
from django.template import loader

from common.api_helpers.utils import create_engine_url


class BrowsableInstructionMixin:
    def get(self, request, *args, **kwargs):
        template = loader.get_template("integration_link.html")
        # TODO Create associative array for integrations
        base_integration_docs_url = create_engine_url("/#/integrations/", override_base=settings.DOCS_URL)
        docs_url = f'{base_integration_docs_url}{request.get_full_path().split("/")[3]}'
        show_button = True
        if request.get_full_path().split("/")[3] == "amazon_sns":
            show_button = False
        source = " ".join(map(lambda x: x.capitalize(), request.get_full_path().split("/")[3].split("_")))
        if request.alert_receive_channel.config.example_payload:
            payload = request.alert_receive_channel.config.example_payload
            payload = json.dumps(payload)
        else:
            payload = "None"
        return HttpResponse(
            template.render(
                {
                    "request": request,
                    "url": request.get_full_path,
                    "docs_url": docs_url,
                    "payload": payload,
                    "source": source,
                    "show_button": show_button,
                }
            )
        )
