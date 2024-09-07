import factory

from apps.mattermost.models import MattermostChannel
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
