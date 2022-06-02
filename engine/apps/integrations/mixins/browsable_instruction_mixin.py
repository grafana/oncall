import json
from urllib.parse import urljoin

from django.conf import settings
from django.http import HttpResponse
from django.template import loader


class BrowsableInstructionMixin:
    def get(self, request, alert_receive_channel, *args, **kwargs):
        template = loader.get_template("integration_link.html")
        # TODO Create associative array for integrations
        base_integration_docs_url = urljoin(settings.DOCS_URL, "/#/integrations/")
        docs_url = f'{base_integration_docs_url}{request.get_full_path().split("/")[3]}'
        show_button = True
        if request.get_full_path().split("/")[3] == "amazon_sns":
            show_button = False
        source = " ".join(map(lambda x: x.capitalize(), request.get_full_path().split("/")[3].split("_")))
        if alert_receive_channel.config.example_payload:
            payload = alert_receive_channel.config.example_payload
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
