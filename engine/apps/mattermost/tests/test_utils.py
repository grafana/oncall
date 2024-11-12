import pytest
from django.conf import settings

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
):
    organization = make_organization()
    token = MattermostEventAuthenticator.create_token(organization=organization)
    settings.MATTERMOST_SIGNING_SECRET = "n0cb4954bec053e6e616febf2c2392ff60bd02c453a52ab53d9a8b0d0d6284a6"
    with pytest.raises(MattermostEventTokenInvalid):
        MattermostEventAuthenticator.verify(token)
