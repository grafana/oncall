import factory

from apps.zoom.models import ZoomChannel, ZoomMessage, ZoomUser
from common.utils import UniqueFaker


class ZoomChannelFactory(factory.DjangoModelFactory):
    channel_id = factory.LazyAttribute(
        lambda v: str(UniqueFaker("pystr", min_chars=5, max_chars=26).generate())
    )
    channel_name = factory.Faker("word")

    class Meta:
        model = ZoomChannel


class ZoomMessageFactory(factory.DjangoModelFactory):
    message_id = factory.LazyAttribute(
        lambda v: str(UniqueFaker("pystr", min_chars=5, max_chars=26).generate())
    )
    channel_id = factory.LazyAttribute(
        lambda v: str(UniqueFaker("pystr", min_chars=5, max_chars=26).generate())
    )

    class Meta:
        model = ZoomMessage


class ZoomUserFactory(factory.DjangoModelFactory):
    zoom_user_id = factory.LazyAttribute(
        lambda v: str(UniqueFaker("pystr", min_chars=5, max_chars=26).generate())
    )
    email = factory.Faker("email")
    display_name = factory.Faker("name")

    class Meta:
        model = ZoomUser
