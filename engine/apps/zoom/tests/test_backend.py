import pytest
from django.conf import settings

# Skip all tests if Zoom integration is not enabled
if not getattr(settings, 'FEATURE_ZOOM_INTEGRATION_ENABLED', False):
    pytest.skip("Zoom integration is not enabled", allow_module_level=True)


@pytest.mark.django_db
def test_zoom_backend_serialize_user_with_zoom_user(
    make_organization,
    make_user_for_organization,
    make_zoom_user,
):
    """Test ZoomBackend.serialize_user when user has Zoom identity."""
    from apps.zoom.backend import ZoomBackend

    organization = make_organization()
    user = make_user_for_organization(organization)
    zoom_user = make_zoom_user(
        user=user,
        zoom_user_id="zoom123",
        email="test@example.com",
        display_name="Test User",
    )

    backend = ZoomBackend()
    result = backend.serialize_user(user)

    assert result is not None
    assert result["zoom_user_id"] == "zoom123"
    assert result["email"] == "test@example.com"
    assert result["display_name"] == "Test User"


@pytest.mark.django_db
def test_zoom_backend_serialize_user_without_zoom_user(
    make_organization,
    make_user_for_organization,
):
    """Test ZoomBackend.serialize_user when user has no Zoom identity."""
    from apps.zoom.backend import ZoomBackend

    organization = make_organization()
    user = make_user_for_organization(organization)

    backend = ZoomBackend()
    result = backend.serialize_user(user)

    assert result is None


@pytest.mark.django_db
def test_zoom_backend_unlink_user(
    make_organization,
    make_user_for_organization,
    make_zoom_user,
):
    """Test ZoomBackend.unlink_user removes Zoom identity."""
    from apps.zoom.backend import ZoomBackend
    from apps.zoom.models import ZoomUser

    organization = make_organization()
    user = make_user_for_organization(organization)
    make_zoom_user(user=user)

    assert ZoomUser.objects.filter(user=user).exists()

    backend = ZoomBackend()
    backend.unlink_user(user)

    assert not ZoomUser.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_zoom_backend_validate_channel_filter_data_valid(
    make_organization,
    make_zoom_channel,
):
    """Test ZoomBackend.validate_channel_filter_data with valid data."""
    from apps.zoom.backend import ZoomBackend

    organization = make_organization()
    channel = make_zoom_channel(organization=organization)

    backend = ZoomBackend()
    data = {
        "enabled": True,
        "channel": channel.public_primary_key,
    }
    result = backend.validate_channel_filter_data(organization, data)

    assert result["enabled"] is True
    assert result["channel"] == channel.public_primary_key


@pytest.mark.django_db
def test_zoom_backend_validate_channel_filter_data_invalid_channel(
    make_organization,
):
    """Test ZoomBackend.validate_channel_filter_data with invalid channel."""
    from rest_framework import serializers
    from apps.zoom.backend import ZoomBackend

    organization = make_organization()

    backend = ZoomBackend()
    data = {
        "enabled": True,
        "channel": "invalid_channel_id",
    }

    with pytest.raises(serializers.ValidationError):
        backend.validate_channel_filter_data(organization, data)
