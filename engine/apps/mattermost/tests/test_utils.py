import pytest

from apps.mattermost.exceptions import MattermostEventTokenInvalid
from apps.mattermost.utils import MattermostEventAuthenticator


@pytest.mark.django_db
def test_jwt_token_validation_success(
    make_organization,
):
    organization = make_organization()
    token = MattermostEventAuthenticator.create_token(organization=organization)
    payload = MattermostEventAuthenticator.verify(token)
    assert payload["organization_id"] == organization.public_primary_key


@pytest.mark.django_db
def test_jwt_token_validation_failure(
    make_organization,
    set_random_mattermost_sigining_secret,
):
    organization = make_organization()
    token = MattermostEventAuthenticator.create_token(organization=organization)
    set_random_mattermost_sigining_secret()
    with pytest.raises(MattermostEventTokenInvalid):
        MattermostEventAuthenticator.verify(token)
