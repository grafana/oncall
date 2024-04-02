import factory

from apps.google.models import GoogleOAuth2User
from common.utils import UniqueFaker


class GoogleOAuth2UserFactory(factory.DjangoModelFactory):
    google_user_id = UniqueFaker("pyint")
    access_token = factory.Faker("password")
    refresh_token = factory.Faker("password")
    oauth_scope = factory.Faker("word")

    class Meta:
        model = GoogleOAuth2User
