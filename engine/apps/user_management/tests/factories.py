import factory

from apps.user_management.models import Organization, Region, Team, User
from common.utils import UniqueFaker


class OrganizationFactory(factory.DjangoModelFactory):
    org_title = factory.Faker("word")
    stack_id = UniqueFaker("pyint")
    org_id = UniqueFaker("pyint")
    stack_slug = factory.Faker("word")

    class Meta:
        model = Organization


class UserFactory(factory.DjangoModelFactory):
    username = UniqueFaker("user_name")
    email = factory.Faker("email")
    user_id = UniqueFaker("pyint")
    avatar_url = factory.Faker("url")

    class Meta:
        model = User


class TeamFactory(factory.DjangoModelFactory):
    name = factory.Faker("user_name")
    email = factory.Faker("email")
    team_id = UniqueFaker("pyint")
    avatar_url = factory.Faker("url")

    class Meta:
        model = Team


class RegionFactory(factory.DjangoModelFactory):
    name = factory.Faker("country")
    slug = factory.Faker("slug")
    oncall_backend_url = factory.Faker("url")

    class Meta:
        model = Region
