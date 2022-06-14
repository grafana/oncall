import pytest
from pytest_factoryboy import register

from apps.user_management.tests.factories import OrganizationFactory, UserFactory

register(UserFactory)
register(OrganizationFactory)


@pytest.fixture()
def make_organization_and_user_with_token(make_organization_and_user, make_public_api_token):
    def _make_organization_and_user_with_token():
        organization, user = make_organization_and_user()
        _, token = make_public_api_token(user, organization)
        return organization, user, token

    return _make_organization_and_user_with_token
