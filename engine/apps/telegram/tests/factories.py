import factory

from apps.telegram.models import (
    TelegramChannelVerificationCode,
    TelegramMessage,
    TelegramToOrganizationConnector,
    TelegramToUserConnector,
    TelegramVerificationCode,
)
from common.utils import UniqueFaker


class TelegramToUserConnectorFactory(factory.DjangoModelFactory):
    telegram_chat_id = UniqueFaker("pyint")

    class Meta:
        model = TelegramToUserConnector


class TelegramChannelFactory(factory.DjangoModelFactory):
    channel_chat_id = factory.LazyAttribute(lambda v: str(UniqueFaker("pyint").generate()))
    channel_name = factory.Faker("word")
    discussion_group_chat_id = factory.LazyAttribute(lambda v: str(UniqueFaker("pyint").generate()))
    discussion_group_name = factory.Faker("word")

    class Meta:
        model = TelegramToOrganizationConnector


class TelegramVerificationCodeFactory(factory.DjangoModelFactory):
    class Meta:
        model = TelegramVerificationCode


class TelegramChannelVerificationCodeFactory(factory.DjangoModelFactory):
    class Meta:
        model = TelegramChannelVerificationCode


class TelegramMessageFactory(factory.DjangoModelFactory):
    message_id = factory.Faker("pyint")
    chat_id = factory.Faker("word")

    class Meta:
        model = TelegramMessage
