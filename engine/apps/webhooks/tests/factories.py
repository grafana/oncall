import factory

from apps.webhooks.models import Webhook, WebhookResponse
from common.utils import UniqueFaker


class CustomWebhookFactory(factory.DjangoModelFactory):

    url = factory.Faker("url")
    name = UniqueFaker("word")

    class Meta:
        model = Webhook


class WebhookResponseFactory(factory.DjangoModelFactory):
    timestamp = factory.Faker("date_time")

    class Meta:
        model = WebhookResponse
