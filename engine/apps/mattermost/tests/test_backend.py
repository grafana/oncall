import pytest
from rest_framework import serializers

from apps.mattermost.backend import MattermostBackend
from apps.user_management.models import User


@pytest.mark.django_db
def test_unlink_user(make_organization_and_user, make_mattermost_user):
    _, user = make_organization_and_user()
    make_mattermost_user(user=user)
    backend = MattermostBackend()
    backend.unlink_user(user)
    user.refresh_from_db()

    with pytest.raises(User.mattermost_user_identity.RelatedObjectDoesNotExist):
        user.mattermost_user_identity


@pytest.mark.django_db
def test_serialize_user(make_organization_and_user, make_mattermost_user):
    _, user = make_organization_and_user()
    mattermost_user = make_mattermost_user(user=user)
    data = MattermostBackend().serialize_user(user)
    assert data["mattermost_user_id"] == mattermost_user.mattermost_user_id
    assert data["username"] == mattermost_user.username


@pytest.mark.django_db
def test_serialize_user_not_found(
    make_organization_and_user,
):
    _, user = make_organization_and_user()
    data = MattermostBackend().serialize_user(user)
    assert data is None


@pytest.mark.django_db
def test_validate_channel_filter_data(
    make_organization,
    make_mattermost_channel,
):
    organization = make_organization()
    channel = make_mattermost_channel(organization=organization, is_default_channel=True)
    input_data = {"channel": channel.public_primary_key, "enabled": True}
    data = MattermostBackend().validate_channel_filter_data(organization=organization, data=input_data)
    assert data["channel"] == channel.public_primary_key
    assert data["enabled"]


@pytest.mark.django_db
def test_validate_channel_filter_data_update_only_channel(
    make_organization,
    make_mattermost_channel,
):
    organization = make_organization()
    channel = make_mattermost_channel(organization=organization, is_default_channel=True)
    input_data = {"channel": channel.public_primary_key}
    data = MattermostBackend().validate_channel_filter_data(organization=organization, data=input_data)
    assert data["channel"] == channel.public_primary_key
    assert "enabled" not in data


@pytest.mark.django_db
@pytest.mark.parametrize(
    "input_data,expected_data",
    [
        ({}, {}),
        ({"enabled": True}, {"enabled": True}),
        ({"enabled": False}, {"enabled": False}),
        ({"enabled": 1}, {"enabled": True}),
        ({"enabled": 0}, {"enabled": False}),
        ({"channel": None, "enabled": True}, {"channel": None, "enabled": True}),
        ({"channel": None}, {"channel": None}),
    ],
)
def test_validate_channel_filter_data_toggle_flag(
    make_organization,
    input_data,
    expected_data,
):
    organization = make_organization()
    data = MattermostBackend().validate_channel_filter_data(organization=organization, data=input_data)
    assert data == expected_data


@pytest.mark.django_db
def test_validate_channel_filter_data_invalid_channel(
    make_organization,
):
    organization = make_organization()
    input_data = {"channel": "abcd", "enabled": True}
    with pytest.raises(serializers.ValidationError):
        MattermostBackend().validate_channel_filter_data(organization=organization, data=input_data)
