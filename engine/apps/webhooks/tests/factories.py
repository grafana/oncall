import factory

from apps.webhooks.models import Webhook
from common.utils import UniqueFaker


class CustomWebhookFactory(factory.DjangoModelFactory):

    url = factory.Faker("url")
    name = UniqueFaker("word")

    class Meta:
        model = Webhook
