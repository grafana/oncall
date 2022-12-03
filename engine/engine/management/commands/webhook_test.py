# from django.apps import apps
from django.core.management import BaseCommand

from apps.webhooks.models import Webhook


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Webhooks = apps.get_model("webhooks", "Webhook")

        webhook = Webhook()
        webhook.name = "Test webhook"

        event_data = {}
        print(webhook.check_trigger(event_data))
        webhook.trigger_template = "false"
        print(webhook.check_trigger(event_data))

        event_data["id"] = 10
        webhook.trigger_template = "{{ id == 10 }}"
        print(webhook.check_trigger(event_data))
        event_data["id"] = 9
        print(webhook.check_trigger(event_data))

        webhook.username = "external-user"
        webhook.password = "soopersecret"
        webhook.http_method = "GET"
        webhook.url = "https://webhook.site/15dc32a7-8d53-4a84-b41b-a290b9fd48e2"
        print(webhook.build_url(event_data))

        # print(webhook.make_request(event_data))
        #
        # webhook.http_method = "POST"
        # print(webhook.make_request(event_data))
        #
        # webhook.http_method = "PUT"
        # print(webhook.make_request(event_data))
        #
        # webhook.http_method = "OPTIONS"
        # print(webhook.make_request(event_data))
        #
        # webhook.http_method = "DELETE"
        # print(webhook.make_request(event_data))

        # webhook.http_method = "GET"
        # webhook.url_template = "https://webhook.site/15dc32a7-8d53-4a84-b41b-a290b9fd48e2/test?id={{id}}"
        # print(webhook.build_url(event_data))
        # print(webhook.make_request(event_data))

        event_data["user"] = {"id": "oncall-user"}
        event_data["alert"] = {
            "alert_uid": "08d6891a-835c-e661-39fa-96b6a9e26552",
            "title": "The whole system is down",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/ee/Grumpy_Cat_by_Gage_Skidmore.jpg",
            "state": "alerting",
            "link_to_upstream_details": "https://en.wikipedia.org/wiki/Downtime",
            "message": "Smth happened. Oh no!",
        }
        webhook.http_method = "POST"
        webhook.username = "external-user"
        webhook.password = "soopersecret"
        print(webhook.make_request(event_data))
