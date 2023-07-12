import pytest

from apps.mobile_app.models import FCMDevice


@pytest.mark.django_db
def test_get_active_device_for_user_works(make_organization_and_user):
    _, user = make_organization_and_user()
    FCMDevice.objects.create(user=user, registration_id="inactive_device_id", active=False)
    active_device = FCMDevice.objects.create(user=user, registration_id="active_device_id", active=True)

    assert FCMDevice.objects.filter(user=user).count() == 2
    assert FCMDevice.get_active_device_for_user(user) == active_device
