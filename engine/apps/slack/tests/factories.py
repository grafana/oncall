import factory

from apps.slack.models import SlackChannel, SlackMessage, SlackTeamIdentity, SlackUserGroup, SlackUserIdentity
from common.utils import UniqueFaker


class SlackTeamIdentityFactory(factory.DjangoModelFactory):
    slack_id = UniqueFaker("sentence", nb_words=3)
    cached_name = factory.Faker("word")

    class Meta:
        model = SlackTeamIdentity


class SlackUserIdentityFactory(factory.DjangoModelFactory):
    slack_id = UniqueFaker("sentence", nb_words=3)
    cached_avatar = "TEST_SLACK_IMAGE_URL"
    cached_name = "TEST_SLACK_NAME"
    cached_slack_login = "TEST_SLACK_LOGIN"

    class Meta:
        model = SlackUserIdentity


class SlackUserGroupFactory(factory.DjangoModelFactory):
    slack_id = UniqueFaker("sentence", nb_words=3)
    name = factory.Faker("word")
    handle = UniqueFaker("sentence", nb_words=3)

    class Meta:
        model = SlackUserGroup


class SlackChannelFactory(factory.DjangoModelFactory):
    slack_id = UniqueFaker("sentence", nb_words=3)
    name = factory.Faker("word")

    class Meta:
        model = SlackChannel


class SlackMessageFactory(factory.DjangoModelFactory):
    slack_id = UniqueFaker("sentence", nb_words=3)
    channel_id = factory.Faker("word")

    class Meta:
        model = SlackMessage
