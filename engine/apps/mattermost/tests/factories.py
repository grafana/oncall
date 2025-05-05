import factory

from apps.mattermost.models import MattermostChannel, MattermostMessage, MattermostUser
from common.utils import UniqueFaker


class MattermostChannelFactory(factory.DjangoModelFactory):
    mattermost_team_id = factory.LazyAttribute(
        lambda v: str(UniqueFaker("pystr", min_chars=5, max_chars=26).generate())
    )
    channel_id = factory.LazyAttribute(lambda v: str(UniqueFaker("pystr", min_chars=5, max_chars=26).generate()))
    channel_name = factory.Faker("word")
    display_name = factory.Faker("word")

    class Meta:
        model = MattermostChannel


class MattermostMessageFactory(factory.DjangoModelFactory):
    post_id = factory.LazyAttribute(lambda v: str(UniqueFaker("pystr", min_chars=5, max_chars=26).generate()))
    channel_id = factory.LazyAttribute(lambda v: str(UniqueFaker("pystr", min_chars=5, max_chars=26).generate()))

    class Meta:
        model = MattermostMessage


class MattermostUserFactory(factory.DjangoModelFactory):
    mattermost_user_id = factory.LazyAttribute(
        lambda v: str(UniqueFaker("pystr", min_chars=5, max_chars=26).generate())
    )
    username = factory.Faker("word")
    nickname = factory.Faker("word")

    class Meta:
        model = MattermostUser
